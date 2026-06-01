"""Build hook for the Wilderness zone (wilderness spec §6).

``build()`` is idempotent — safe to call at first boot and on season reset.
Evennia is imported lazily inside ``build()`` so importing this module stays
Evennia-free for pure-data test suites.
"""

from __future__ import annotations

from world.zones.wilderness.npcs import NPCS, PLACEMENT
from world.zones.wilderness.xymap import XYMAP_DATA


def build() -> None:
    """Spawn the xyzgrid wilderness map, tag rooms, wire inter-zone exits, place NPC."""
    from evennia.contrib.grid.xyzgrid.xyzgrid import get_xyzgrid  # noqa: PLC0415

    grid = get_xyzgrid()
    grid.add_maps(XYMAP_DATA)
    grid.reload()
    grid.spawn(xyz=("*", "*", "wilderness"))

    _tag_rooms()
    _wire_interzone_exits()
    _build_npcs()


def _tag_rooms() -> None:
    """Tag each xyzgrid wilderness room with its stable zone identity tag.

    Adding ``"wilderness:<room_key>"`` in the ``ROOM_CATEGORY`` lets the
    standard builder helpers (and the Keep's deferred exit wiring) locate
    wilderness rooms the same way they find Keep rooms.
    """
    from evennia.contrib.grid.xyzgrid.xyzroom import XYZRoom  # noqa: PLC0415

    from world.zones.builder import ROOM_CATEGORY  # noqa: PLC0415

    for room in XYZRoom.objects.filter_xyz(("*", "*", "wilderness")):
        room_key: object = room.db.room_key
        if room_key:
            tag_str = f"wilderness:{room_key}"
            if not room.tags.has(tag_str, category=ROOM_CATEGORY):
                room.tags.add(tag_str, category=ROOM_CATEGORY)


def _wire_interzone_exits() -> None:
    """Create exits that bridge the wilderness to neighbouring zones (spec §8).

    Non-cardinal exit keys prevent the xyzgrid spawner from deleting them.
    Cardinal aliases let players type the intuitive direction. Deferred targets
    (Caves not yet built at M8) are skipped silently.
    """
    from evennia.utils import create  # noqa: PLC0415
    from evennia.utils.search import search_object_by_tag  # noqa: PLC0415

    from world.zones.builder import EXIT_CATEGORY, ROOM_CATEGORY  # noqa: PLC0415

    _exits: list[tuple[str, str, str, list[str]]] = [
        # (source_room_key, exit_key, target_zone:room_key, aliases)
        ("keep_road", "gate", "keep:main_gate", ["n", "north"]),
        ("ravine_mouth", "enter", "caves:ravine_mouth", ["e", "east"]),
        # Cave of the Unknown is a sealed v1 stub (CLAUDE.md): the target room
        # never exists in v1, so this exit is always skipped silently. It records
        # the spec's inter-zone link (wilderness.md §exits) for if/when the
        # `unknown` zone is ever built. No cardinal alias (InterruptMapNode).
        ("sealed_cleft", "cleft", "unknown:entrance", []),
    ]

    for src_key, exit_key, target_tag, aliases in _exits:
        source_matches = search_object_by_tag(f"wilderness:{src_key}", category=ROOM_CATEGORY)
        if not source_matches:
            continue
        source = source_matches[0]

        target_matches = search_object_by_tag(target_tag, category=ROOM_CATEGORY)
        if not target_matches:
            continue
        target = target_matches[0]

        identity = f"wilderness:{src_key}:{exit_key}"
        existing = search_object_by_tag(identity, category=EXIT_CATEGORY)
        if not existing:
            exit_obj = create.create_object(
                "typeclasses.exits.Exit",
                key=exit_key,
                location=source,
                destination=target,
                aliases=aliases,
            )
            exit_obj.tags.add(identity, category=EXIT_CATEGORY)

    # Re-run Keep exit wiring now that wilderness:keep_road is tagged and findable.
    # This creates the south exit from main_gate → keep_road that was deferred
    # during the Keep build (see test_keep_build.py::test_main_gate_wilderness_exit_skipped).
    from world.zones import keep  # noqa: PLC0415
    from world.zones.builder import build_exits  # noqa: PLC0415

    build_exits("keep", keep.EXITS)


def _build_npcs() -> None:
    """Place static wilderness NPCs (the Mad Hermit) idempotently."""
    from world.zones.builder import build_npcs  # noqa: PLC0415

    build_npcs("wilderness", NPCS, PLACEMENT)
