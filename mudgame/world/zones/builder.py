"""Idempotent world-builder shared by every zone's thin ``build()`` hook.

Translates the pure room/exit data lists into live Evennia objects (zones spec
R1 §2). Identity is keyed by a stable ``"<zone>:<key>"`` tag, so a second run
*updates* the existing room/exit rather than duplicating it — the milestone
build and the season-reset rebuild (R6) share one path.

This module imports Evennia; the data modules it consumes do not.
"""

from __future__ import annotations

from typing import Any

from evennia.utils import create
from evennia.utils.search import search_object_by_tag

from world.zones.records import ExitRecord, NpcRecord, RoomRecord

ROOM_CATEGORY = "zone_room"
EXIT_CATEGORY = "zone_exit"
NPC_CATEGORY = "zone_npc"
OBJECT_CATEGORY = "zone_object"
FLAG_CATEGORY = "room_flag"
ROOM_TYPECLASS = "typeclasses.rooms.Room"
EXIT_TYPECLASS = "typeclasses.exits.Exit"
NPC_TYPECLASS = "typeclasses.npcs.ServiceNpc"

# Tag (category None) marking the server-wide recall destination, matched by
# PlayerCharacter._find_recall_room via search_object_by_tag("inner_bailey").
RECALL_TAG = "inner_bailey"

# Tag (category None) marking the chapel-staff pool the disguised-priest plot
# rotates its seasonal spy through (disguised-priest.md §2); the M12
# priest_manager finds the pool via search_object_by_tag(PRIEST_POOL_TAG).
PRIEST_POOL_TAG = "priest_pool"


def _zonekey(zone: str, key: str) -> str:
    """Stable global identity for a room: ``"<zone>:<key>"``."""
    return f"{zone}:{key}"


def _find_tagged(tag_key: str, category: str) -> Any:
    """Return the first object carrying ``tag_key`` in ``category``, or None."""
    matches = search_object_by_tag(tag_key, category=category)
    return matches[0] if matches else None


def _resolve_target(zone: str, to: str) -> Any:
    """Resolve an exit target. ``"<zone>:<key>"`` is inter-zone; else intra-zone."""
    identity = to if ":" in to else _zonekey(zone, to)
    return _find_tagged(identity, ROOM_CATEGORY)


def _apply_flag(room: Any, record: RoomRecord, flag: str) -> None:
    """Add or remove a room-flag tag to mirror the record (idempotent)."""
    if record.get(flag):
        room.tags.add(flag, category=FLAG_CATEGORY)
    elif room.tags.has(flag, category=FLAG_CATEGORY):
        room.tags.remove(flag, category=FLAG_CATEGORY)


def build_rooms(zone: str, rooms: list[RoomRecord]) -> None:
    """Create or update every room in ``rooms`` under ``zone`` (idempotent)."""
    for record in rooms:
        identity = _zonekey(zone, record["key"])
        room = _find_tagged(identity, ROOM_CATEGORY)
        if room is None:
            room = create.create_object(ROOM_TYPECLASS, key=record["name"])
            room.tags.add(identity, category=ROOM_CATEGORY)
        room.key = record["name"]
        room.db.desc = record["desc"]
        room.db.zone = zone
        room.db.room_key = record["key"]
        _apply_flag(room, record, "dark")
        _apply_flag(room, record, "no_recall")


def build_exits(zone: str, exits: list[ExitRecord]) -> None:
    """Wire every exit in ``exits`` (idempotent).

    Inter-zone exits whose target room is not yet built are skipped silently;
    the world builder wires them once both zones exist.
    """
    for record in exits:
        source = _find_tagged(_zonekey(zone, record["from"]), ROOM_CATEGORY)
        if source is None:
            continue
        destination = _resolve_target(zone, record["to"])
        if destination is None:
            continue
        identity = f"{zone}:{record['from']}:{record['dir']}"
        exit_obj = _find_tagged(identity, EXIT_CATEGORY)
        if exit_obj is None:
            exit_obj = create.create_object(
                EXIT_TYPECLASS,
                key=record["dir"],
                location=source,
                destination=destination,
                aliases=record.get("aliases"),
            )
            exit_obj.tags.add(identity, category=EXIT_CATEGORY)
        else:
            exit_obj.location = source
            exit_obj.destination = destination


def _npc_identity(zone: str, npc_key: str) -> str:
    """Stable global identity for a static NPC: ``"<zone>:npc:<key>"``."""
    return f"{zone}:npc:{npc_key}"


def find_npc(zone: str, npc_key: str) -> Any:
    """Return the live NPC object for ``zone:npc_key``, or None if unbuilt."""
    return _find_tagged(_npc_identity(zone, npc_key), NPC_CATEGORY)


def build_npcs(zone: str, npcs: list[NpcRecord], placement: dict[str, str]) -> None:
    """Create or update every static NPC and place it in its room (idempotent).

    ``placement`` maps each NPC ``key`` to the room ``key`` it stands in. An NPC
    whose room is not built (or not placed) is skipped silently, mirroring the
    deferred-target handling in ``build_exits``.
    """
    for record in npcs:
        room_key = placement.get(record["key"])
        if room_key is None:
            continue
        room = _find_tagged(_zonekey(zone, room_key), ROOM_CATEGORY)
        if room is None:
            continue
        identity = _npc_identity(zone, record["key"])
        npc = _find_tagged(identity, NPC_CATEGORY)
        if npc is None:
            npc = create.create_object(NPC_TYPECLASS, key=record["name"], location=room)
            npc.tags.add(identity, category=NPC_CATEGORY)
        npc.key = record["name"]
        npc.location = room
        npc.db.npc_key = record["key"]
        npc.db.sdesc = record["sdesc"]
        npc.db.role = record["role"]
        # Quest-giver key (world-build §8): set on a giver NPC, None otherwise.
        # Written unconditionally so a rebuild that drops the key clears it.
        npc.db.giver_key = record.get("giver_key")
        inventory = record.get("inventory")
        if inventory is not None:
            npc.db.inventory = list(inventory)


def _object_identity(zone: str, room_key: str, slug: str) -> str:
    """Stable global identity for a placed zone object: ``"<zone>:<room>:<slug>"``."""
    return f"{zone}:{room_key}:{slug}"


def find_object(zone: str, room_key: str, slug: str) -> Any:
    """Return the live placed object for ``zone:room_key:slug``, or None."""
    return _find_tagged(_object_identity(zone, room_key, slug), OBJECT_CATEGORY)


def build_object(zone: str, room_key: str, slug: str, typeclass: str, key: str) -> Any:
    """Place a single unique object in a room (idempotent).

    Returns the existing object if already placed, None if its room is not yet
    built (deferred, mirroring build_exits/build_npcs), else the freshly created
    object tagged with its stable identity so a rebuild never duplicates it.
    """
    existing = find_object(zone, room_key, slug)
    if existing is not None:
        return existing
    room = _find_tagged(_zonekey(zone, room_key), ROOM_CATEGORY)
    if room is None:
        return None
    obj = create.create_object(typeclass, key=key, location=room)
    obj.tags.add(_object_identity(zone, room_key, slug), category=OBJECT_CATEGORY)
    return obj


def build_zone(zone: str, rooms: list[RoomRecord], exits: list[ExitRecord]) -> None:
    """Build a whole zone: rooms first, then exits (idempotent)."""
    build_rooms(zone, rooms)
    build_exits(zone, exits)


def tag_recall_point(zone: str, room_key: str) -> None:
    """Mark ``zone:room_key`` as the server-wide recall destination."""
    room = _find_tagged(_zonekey(zone, room_key), ROOM_CATEGORY)
    if room is not None and not room.tags.has(RECALL_TAG):
        room.tags.add(RECALL_TAG)


def tag_priest_pool(zone: str, npc_keys: tuple[str, ...]) -> None:
    """Mark each built NPC in ``npc_keys`` as a disguised-priest pool member."""
    for npc_key in npc_keys:
        npc = find_npc(zone, npc_key)
        if npc is not None and not npc.tags.has(PRIEST_POOL_TAG):
            npc.tags.add(PRIEST_POOL_TAG)
