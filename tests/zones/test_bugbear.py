"""Bugbear lair tests — M10 tribe: bugbear.

Derived from docs/specs/zones/caves.md §Cave F and the M9 kobold test shape.
Pure-data groups validate rooms/exits/mobs/spawns without booting Evennia;
engine groups (pytest-django) verify build() and the M6 leadership-halt +
M4 faction-standing wiring.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from typing import Any

import pytest

from world.factions.config import FACTIONS
from world.repop import config as repop_cfg
from world.zones.caves import bugbear
from world.zones.spawn_registry import spawn_points

BUGBEAR_LAIR_ROOMS: frozenset[str] = frozenset(
    {
        "bugbear_mouth",
        "bugbear_passage",
        "bugbear_barracks",
        "bugbear_hold",
        "bugbear_treasury",
        "bugbear_shaman",
        "bugbear_chief",
    }
)


# ---------------------------------------------------------------------------
# Group 1 — Standard tribe interface
# ---------------------------------------------------------------------------


def test_tribe_exposes_standard_interface() -> None:
    assert callable(bugbear.build)
    assert isinstance(bugbear.ROOMS, list)
    assert isinstance(bugbear.EXITS, list)
    assert isinstance(bugbear.MOB_TEMPLATES, list)
    assert isinstance(bugbear.SPAWNS, list)
    assert isinstance(bugbear.NPCS, list)


# ---------------------------------------------------------------------------
# Group 2 — Room / exit data integrity
# ---------------------------------------------------------------------------


def test_room_keys_unique() -> None:
    keys = [r["key"] for r in bugbear.ROOMS]
    assert len(keys) == len(set(keys)), "duplicate room key in bugbear ROOMS"


def test_expected_rooms_present() -> None:
    keys = {r["key"] for r in bugbear.ROOMS}
    assert keys == BUGBEAR_LAIR_ROOMS


def test_all_lair_rooms_are_dark() -> None:
    for room in bugbear.ROOMS:
        assert room.get("dark") is True, f"{room['key']} should be dark"


def test_no_dangling_exits() -> None:
    room_keys = {r["key"] for r in bugbear.ROOMS} | {"ravine_south"}
    for exit_ in bugbear.EXITS:
        src = exit_["from"]
        dst = exit_["to"]
        if ":" not in src:
            assert src in room_keys, f"exit from unknown room {src!r}"
        if ":" not in dst:
            assert dst in room_keys, f"exit to unknown room {dst!r}"


def test_entrance_exits_off_ravine_south() -> None:
    from_south = [e for e in bugbear.EXITS if e["from"] == "ravine_south"]
    to_south = [e for e in bugbear.EXITS if e["to"] == "ravine_south"]
    assert from_south, "no exit from ravine_south into the bugbear lair"
    assert to_south, "no return exit back to ravine_south"


def test_exit_directions_are_reversible() -> None:
    from world.zones.caves._hub import REVERSE  # noqa: PLC0415

    pairs: dict[tuple[str, str], str] = {}
    for exit_ in bugbear.EXITS:
        key = (exit_["from"], exit_["to"])
        pairs[key] = exit_["dir"]
    for (src, dst), direction in pairs.items():
        rev_key = (dst, src)
        assert rev_key in pairs, f"no reverse exit for {src!r} → {dst!r}"
        assert pairs[rev_key] == REVERSE[direction], (
            f"reverse of {direction!r} should be {REVERSE[direction]!r}"
        )


# ---------------------------------------------------------------------------
# Group 3 — Mob templates
# ---------------------------------------------------------------------------


def test_mob_factions_are_valid_ids() -> None:
    valid = set(FACTIONS.keys())
    for mob in bugbear.MOB_TEMPLATES:
        assert mob["faction"] in valid, f"mob {mob['key']!r} bad faction {mob['faction']!r}"


def test_all_bugbear_mobs_use_bugbear_faction() -> None:
    assert all(m["faction"] == "bugbear" for m in bugbear.MOB_TEMPLATES)


def test_mob_ascending_ac_in_range() -> None:
    for mob in bugbear.MOB_TEMPLATES:
        assert mob["ac"] >= 10, f"mob {mob['key']!r} AC {mob['ac']} below ascending base 10"


def test_mob_keys_unique() -> None:
    keys = [m["key"] for m in bugbear.MOB_TEMPLATES]
    assert len(keys) == len(set(keys))


# ---------------------------------------------------------------------------
# Group 4 — Spawns + leadership
# ---------------------------------------------------------------------------


def test_spawn_templates_are_defined() -> None:
    mob_keys = {m["key"] for m in bugbear.MOB_TEMPLATES}
    for spawn in bugbear.SPAWNS:
        assert spawn["template"] in mob_keys, (
            f"spawn in {spawn['room']!r} references unknown template {spawn['template']!r}"
        )


def test_spawn_rooms_exist() -> None:
    room_keys = {r["key"] for r in bugbear.ROOMS}
    for spawn in bugbear.SPAWNS:
        assert spawn["room"] in room_keys, f"spawn references unknown room {spawn['room']!r}"


def test_tribe_has_exactly_one_chief_and_one_shaman() -> None:
    roles = [s.get("leader_role") for s in bugbear.SPAWNS if s.get("is_leader")]
    assert roles.count("chief") == 1, "bugbear tribe needs exactly one chief spawn"
    assert roles.count("shaman") == 1, "bugbear tribe needs exactly one shaman spawn"


def test_leader_spawns_are_single_and_well_formed() -> None:
    for spawn in bugbear.SPAWNS:
        if spawn.get("is_leader"):
            assert spawn.get("leader_role") in {"chief", "shaman"}
            assert spawn["count"] == 1, "a leader spawn must be a single mob"


# ---------------------------------------------------------------------------
# Group 5 — Repop spawn-point derivation (pure, no Evennia)
# ---------------------------------------------------------------------------


def test_spawn_points_expand_count() -> None:
    points = spawn_points("caves", bugbear.SPAWNS, bugbear.MOB_TEMPLATES)
    assert len(points) == sum(s["count"] for s in bugbear.SPAWNS)


def test_spawn_point_ids_are_unique() -> None:
    points = spawn_points("caves", bugbear.SPAWNS, bugbear.MOB_TEMPLATES)
    ids = [p.spawn_id for p in points]
    assert len(ids) == len(set(ids))


def test_spawn_points_resolve_faction_from_template() -> None:
    faction_by_template = {m["key"]: m["faction"] for m in bugbear.MOB_TEMPLATES}
    for point in spawn_points("caves", bugbear.SPAWNS, bugbear.MOB_TEMPLATES):
        assert point.faction == faction_by_template[point.mob_template]


def test_derived_points_have_one_chief_and_one_shaman() -> None:
    points = spawn_points("caves", bugbear.SPAWNS, bugbear.MOB_TEMPLATES)
    leaders = [p for p in points if p.is_leader]
    roles = [p.leader_role for p in leaders]
    assert roles.count("chief") == 1
    assert roles.count("shaman") == 1
    assert all(p.faction == "bugbear" for p in leaders)


def test_spawn_point_room_is_zone_namespaced() -> None:
    for point in spawn_points("caves", bugbear.SPAWNS, bugbear.MOB_TEMPLATES):
        assert point.room.startswith("caves:")


def test_designated_rival_is_hobgoblin() -> None:
    assert repop_cfg.DESIGNATED_RIVAL.get("bugbear") == "hobgoblin"


# ---------------------------------------------------------------------------
# Engine tests — build() materialises the lair
# ---------------------------------------------------------------------------


def _bugbear_rooms() -> list[Any]:
    from evennia.utils.search import search_object_by_tag  # noqa: PLC0415

    from world.zones.builder import ROOM_CATEGORY  # noqa: PLC0415

    return [r for r in search_object_by_tag(category=ROOM_CATEGORY) if r.db.zone == "caves"]


def _bugbear_exits() -> list[Any]:
    from evennia.utils.search import search_object_by_tag  # noqa: PLC0415

    from world.zones.builder import EXIT_CATEGORY  # noqa: PLC0415

    out = []
    for e in search_object_by_tag(category=EXIT_CATEGORY):
        loc = e.location
        if loc is not None and loc.db.zone == "caves":
            out.append(e)
    return out


def _find_room(room_key: str) -> Any:
    from evennia.utils.search import search_object_by_tag  # noqa: PLC0415

    from world.zones.builder import ROOM_CATEGORY  # noqa: PLC0415

    matches = search_object_by_tag(f"caves:{room_key}", category=ROOM_CATEGORY)
    return matches[0] if matches else None


@pytest.fixture
def built_bugbear() -> Iterator[None]:
    """Build hub + bugbear lair, yield, then tear down."""
    from world.zones import caves  # noqa: PLC0415

    caves.build()
    try:
        yield
    finally:
        for exit_ in _bugbear_exits():
            exit_.delete()
        for room in _bugbear_rooms():
            room.delete()


@pytest.mark.django_db
def test_build_creates_all_lair_rooms(built_bugbear: None) -> None:
    built = {r.db.room_key for r in _bugbear_rooms()}
    assert built >= BUGBEAR_LAIR_ROOMS


@pytest.mark.django_db
def test_build_is_idempotent(built_bugbear: None) -> None:
    from world.zones import caves  # noqa: PLC0415

    first_rooms = {r.id for r in _bugbear_rooms()}
    first_exits = {e.id for e in _bugbear_exits()}
    caves.build()
    assert {r.id for r in _bugbear_rooms()} == first_rooms
    assert {e.id for e in _bugbear_exits()} == first_exits


@pytest.mark.django_db
def test_lair_rooms_get_dark_flag(built_bugbear: None) -> None:
    from world.zones.builder import FLAG_CATEGORY  # noqa: PLC0415

    mouth = _find_room("bugbear_mouth")
    assert mouth is not None
    assert mouth.tags.has("dark", category=FLAG_CATEGORY)

    chief = _find_room("bugbear_chief")
    assert chief is not None
    assert chief.tags.has("dark", category=FLAG_CATEGORY)


@pytest.mark.django_db
def test_internal_exit_is_reversible(built_bugbear: None) -> None:
    mouth = _find_room("bugbear_mouth")
    passage = _find_room("bugbear_passage")
    north = [e for e in mouth.exits if e.key == "n"]
    assert north and north[0].destination == passage
    south = [e for e in passage.exits if e.key == "s"]
    assert south and south[0].destination == mouth


# ---------------------------------------------------------------------------
# Engine tests — leadership halt + rival scouting (repop.md §3-4)
# ---------------------------------------------------------------------------


@pytest.fixture
def repop_and_factions() -> Iterator[tuple[Any, Any]]:
    from evennia.utils import create  # noqa: PLC0415

    from world.zones import caves  # noqa: PLC0415

    repop = create.create_script("world.managers.repop_manager.RepopManager")
    factions = create.create_script("world.managers.faction_manager.FactionManager")
    repop.register_zone("caves", caves.SPAWNS, caves.MOB_TEMPLATES)
    try:
        yield repop, factions
    finally:
        repop.delete()
        factions.delete()


def _bugbear_leaders() -> tuple[Any, Any]:
    from world.zones import caves  # noqa: PLC0415

    points = spawn_points("caves", caves.SPAWNS, caves.MOB_TEMPLATES)
    chief = next(p for p in points if p.leader_role == "chief" and p.faction == "bugbear")
    shaman = next(p for p in points if p.leader_role == "shaman" and p.faction == "bugbear")
    return chief, shaman


def _make_leader_mob(spawn_id: str, key: str, room: Any) -> Any:
    from evennia.utils import create  # noqa: PLC0415

    mob = create.create_object("typeclasses.npcs.Mob", key=key, location=room)
    mob.db.spawn_id = spawn_id
    mob.db.faction_id = "bugbear"
    return mob


@pytest.mark.django_db
def test_killing_one_bugbear_leader_does_not_halt(
    repop_and_factions: tuple[Any, Any],
) -> None:
    from evennia.utils import create  # noqa: PLC0415

    repop, _ = repop_and_factions
    chief, _shaman = _bugbear_leaders()
    room = create.create_object("typeclasses.rooms.Room", key="bugbear-halt-room-1")
    try:
        chief_mob = _make_leader_mob(chief.spawn_id, "Grosh", room)
        chief_mob.at_death()
        assert chief.spawn_id in (repop.db.respawn_at or {})
        assert "bugbear" not in (repop.db.halted_until or {})
        assert not (repop.db.scouts or {})
    finally:
        room.delete()


@pytest.mark.django_db
def test_killing_both_bugbear_leaders_halts_and_scouts(
    repop_and_factions: tuple[Any, Any],
) -> None:
    """Chief + shaman both dead → bugbear repop freezes; hobgoblins scout in."""
    from evennia.utils import create  # noqa: PLC0415

    repop, factions = repop_and_factions
    chief, shaman = _bugbear_leaders()
    baseline_tension = factions.get_tension("bugbear", "hobgoblin")
    room = create.create_object("typeclasses.rooms.Room", key="bugbear-halt-room-2")
    try:
        chief_mob = _make_leader_mob(chief.spawn_id, "Grosh", room)
        shaman_mob = _make_leader_mob(shaman.spawn_id, "Hrak", room)

        chief_mob.at_death()
        shaman_mob.at_death()

        halted_until = (repop.db.halted_until or {}).get("bugbear")
        assert halted_until is not None and halted_until > time.time()

        scouts = repop.db.scouts or {}
        assert len(scouts) == repop_cfg.SCOUT_PARTY_SIZE
        assert all(s["faction"] == "hobgoblin" for s in scouts.values())
        assert all(s["scouting"] == "bugbear" for s in scouts.values())

        assert factions.get_tension("bugbear", "hobgoblin") > baseline_tension
    finally:
        room.delete()


# ---------------------------------------------------------------------------
# Engine tests — faction standing shifts (faction.md §2.1, §5)
# ---------------------------------------------------------------------------


def _teardown_room(room: Any, *characters: Any) -> None:
    for obj in list(room.contents):
        if obj.pk is not None:
            obj.delete()
    room.delete()
    for char in characters:
        if char.pk is not None:
            char.delete()


def _make_bugbear_mob(room: Any, key: str = "bugbear-grunt", *, is_leader: bool = False) -> Any:
    from evennia.utils import create  # noqa: PLC0415

    mob = create.create_object("typeclasses.npcs.Mob", key=key, location=room)
    mob.db.faction_id = "bugbear"
    mob.db.is_leader = is_leader
    return mob


@pytest.mark.django_db
def test_killing_bugbear_member_lowers_player_standing(
    repop_and_factions: tuple[Any, Any],
) -> None:
    from world.factions.config import STANDING_EVENTS  # noqa: PLC0415

    _, factions = repop_and_factions
    from evennia.utils import create  # noqa: PLC0415

    room = create.create_object("typeclasses.rooms.Room", key="bugbear-standing-room-1")
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="bugbear-slayer-1")
    try:
        assert factions.get_standing("bugbear", str(char.id)) == 0
        mob = _make_bugbear_mob(room)
        mob.db.last_attacker = char
        mob.at_death()
        assert factions.get_standing("bugbear", str(char.id)) == STANDING_EVENTS["kill_member"]
    finally:
        _teardown_room(room, char)


@pytest.mark.django_db
def test_killing_bugbear_leader_lowers_standing_more(
    repop_and_factions: tuple[Any, Any],
) -> None:
    from world.factions.config import STANDING_EVENTS  # noqa: PLC0415

    _, factions = repop_and_factions
    from evennia.utils import create  # noqa: PLC0415

    room = create.create_object("typeclasses.rooms.Room", key="bugbear-standing-room-2")
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="bugbear-slayer-2")
    try:
        chief = _make_bugbear_mob(room, key="Grosh", is_leader=True)
        chief.db.last_attacker = char
        chief.at_death()
        assert factions.get_standing("bugbear", str(char.id)) == STANDING_EVENTS["kill_leader"]
    finally:
        _teardown_room(room, char)


@pytest.mark.django_db
def test_unattributed_bugbear_death_does_not_shift_standing(
    repop_and_factions: tuple[Any, Any],
) -> None:
    _, factions = repop_and_factions
    from evennia.utils import create  # noqa: PLC0415

    room = create.create_object("typeclasses.rooms.Room", key="bugbear-standing-room-3")
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="bugbear-bystander")
    try:
        mob = _make_bugbear_mob(room)
        mob.at_death()
        assert factions.get_standing("bugbear", str(char.id)) == 0
    finally:
        _teardown_room(room, char)


@pytest.mark.django_db
def test_bugbear_kills_drive_standing_to_kos_and_bugbear_aggros(
    repop_and_factions: tuple[Any, Any],
) -> None:
    """Enough bugbear kills turn the tribe kill-on-sight; a fresh bugbear attacks."""
    _, factions = repop_and_factions
    from evennia.utils import create  # noqa: PLC0415

    room = create.create_object("typeclasses.rooms.Room", key="bugbear-kos-room")
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="bugbear-scourge")
    try:
        for i in range(10):
            mob = _make_bugbear_mob(room, key=f"bugbear-grunt-{i}")
            mob.db.last_attacker = char
            mob.at_death()
        assert factions.standing_band("bugbear", str(char.id)) == "kill-on-sight"

        _make_bugbear_mob(room, key="bugbear-guard-survivor")
        messages: list[str] = []
        char.msg = lambda text, **_kw: messages.append(str(text))
        char.move_to(room, quiet=True)
        assert any("attacks" in m.lower() for m in messages)
    finally:
        _teardown_room(room, char)
