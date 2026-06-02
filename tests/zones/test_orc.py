"""Orc lair tests — Cave B (Vile Rune, orc_vol) and Cave C (Decapitator, orc_dec).

Derived from docs/specs/zones/caves.md §Cave B-C and the fanout-harness.md §6
task template. Pure-data groups validate static room/exit/mob/spawn data without
booting Evennia; engine groups (pytest-django) verify build() and the M4↔zone
faction/repop wiring.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from typing import Any

import pytest

from world.factions.config import FACTIONS, INITIAL_RELATIONS, RELATION_LADDER, band_for
from world.repop import config as repop_cfg
from world.zones import caves
from world.zones.caves import discovery, orc
from world.zones.spawn_registry import spawn_points

ORC_VOL_ROOMS: frozenset[str] = frozenset(
    {
        "orc_vol_mouth",
        "orc_vol_guard",
        "orc_vol_barracks",
        "orc_vol_warrens",
        "orc_vol_shaman",
        "orc_vol_war_room",
        "orc_vol_chief",
    }
)

ORC_DEC_ROOMS: frozenset[str] = frozenset(
    {
        "orc_dec_mouth",
        "orc_dec_guard",
        "orc_dec_hall",
        "orc_dec_totem",
        "orc_dec_shaman",
        "orc_dec_prison",
        "orc_dec_chief",
    }
)

ALL_ORC_ROOMS = ORC_VOL_ROOMS | ORC_DEC_ROOMS


# ---------------------------------------------------------------------------
# Group 1 — Standard tribe interface (pure)
# ---------------------------------------------------------------------------


def test_orc_package_exposes_standard_interface() -> None:
    assert callable(orc.build)
    assert isinstance(orc.ROOMS, list)
    assert isinstance(orc.EXITS, list)
    assert isinstance(orc.MOB_TEMPLATES, list)
    assert isinstance(orc.SPAWNS, list)
    assert isinstance(orc.NPCS, list)


def test_discovery_finds_orc_tribe() -> None:
    names = [m.__name__.rsplit(".", 1)[-1] for m in discovery.tribes()]
    assert "orc" in names


# ---------------------------------------------------------------------------
# Group 2 — Room / exit data integrity (pure)
# ---------------------------------------------------------------------------


def test_orc_room_keys_unique() -> None:
    keys = [r["key"] for r in orc.ROOMS]
    assert len(keys) == len(set(keys)), "duplicate room key in orc ROOMS"


def test_expected_orc_vol_rooms_present() -> None:
    keys = {r["key"] for r in orc.ROOMS}
    assert keys >= ORC_VOL_ROOMS, f"missing Vile Rune rooms: {ORC_VOL_ROOMS - keys}"


def test_expected_orc_dec_rooms_present() -> None:
    keys = {r["key"] for r in orc.ROOMS}
    assert keys >= ORC_DEC_ROOMS, f"missing Decapitator rooms: {ORC_DEC_ROOMS - keys}"


def test_orc_lair_rooms_are_dark() -> None:
    by_key = {r["key"]: r for r in orc.ROOMS}
    for key in ALL_ORC_ROOMS:
        assert by_key[key].get("dark") is True, f"{key} should be dark"


def test_no_dangling_orc_intra_zone_exits() -> None:
    room_keys = {r["key"] for r in orc.ROOMS}
    all_rooms = {r["key"] for r in caves.ROOMS}
    for exit_ in orc.EXITS:
        src = exit_["from"]
        dst = exit_["to"]
        if ":" in dst:
            continue
        assert src in all_rooms, f"exit from unknown room {src!r}"
        assert dst in all_rooms, f"exit to unknown room {dst!r}"
    _ = room_keys  # rooms used for the data-integrity check above


def test_ravine_north_connects_to_both_orc_mouths() -> None:
    """Both orc entrances attach to the north ledge (caves spec §ravine)."""
    from_north = {e["to"] for e in orc.EXITS if e["from"] == "ravine_north"}
    assert "orc_vol_mouth" in from_north, "Vile Rune cave mouth not off ravine_north"
    assert "orc_dec_mouth" in from_north, "Decapitator cave mouth not off ravine_north"


def test_orc_exits_are_bidirectional() -> None:
    """Each link must appear in both directions (expand produces both)."""
    pairs: set[tuple[str, str]] = set()
    for e in orc.EXITS:
        pairs.add((e["from"], e["to"]))
    for src, dst in list(pairs):
        assert (dst, src) in pairs, f"exit {src!r} -> {dst!r} has no return"


# ---------------------------------------------------------------------------
# Group 3 — Mob templates (pure)
# ---------------------------------------------------------------------------


def test_orc_mob_keys_unique() -> None:
    keys = [m["key"] for m in orc.MOB_TEMPLATES]
    assert len(keys) == len(set(keys))


def test_orc_vol_mobs_use_orc_vol_faction() -> None:
    vol_mobs = [m for m in orc.MOB_TEMPLATES if m["faction"] == "orc_vol"]
    assert vol_mobs, "no orc_vol mobs defined"
    keys = {m["key"] for m in vol_mobs}
    assert "orc_vol_warrior" in keys
    assert "orc_vol_chief" in keys
    assert "orc_vol_shaman" in keys


def test_orc_dec_mobs_use_orc_dec_faction() -> None:
    dec_mobs = [m for m in orc.MOB_TEMPLATES if m["faction"] == "orc_dec"]
    assert dec_mobs, "no orc_dec mobs defined"
    keys = {m["key"] for m in dec_mobs}
    assert "orc_dec_warrior" in keys
    assert "orc_dec_chief" in keys
    assert "orc_dec_shaman" in keys


def test_orc_mob_factions_are_valid_ids() -> None:
    valid = set(FACTIONS.keys())
    for mob in orc.MOB_TEMPLATES:
        assert mob["faction"] in valid, f"mob {mob['key']!r} bad faction {mob['faction']!r}"


def test_orc_mob_ascending_ac_in_range() -> None:
    for mob in orc.MOB_TEMPLATES:
        assert mob["ac"] >= 10, f"mob {mob['key']!r} AC {mob['ac']} below ascending base 10"


# ---------------------------------------------------------------------------
# Group 4 — Spawns + leadership (pure)
# ---------------------------------------------------------------------------


def test_orc_spawn_templates_defined() -> None:
    mob_keys = {m["key"] for m in orc.MOB_TEMPLATES}
    for spawn in orc.SPAWNS:
        assert spawn["template"] in mob_keys, (
            f"spawn in {spawn['room']!r} references unknown template {spawn['template']!r}"
        )


def test_orc_spawn_rooms_exist() -> None:
    all_room_keys = {r["key"] for r in caves.ROOMS}
    for spawn in orc.SPAWNS:
        assert spawn["room"] in all_room_keys, f"spawn references unknown room {spawn['room']!r}"


def test_orc_vol_tribe_has_exactly_one_chief_and_one_shaman() -> None:
    vol_spawns = [s for s in orc.SPAWNS if s.get("is_leader") and s["room"].startswith("orc_vol")]
    roles = [s.get("leader_role") for s in vol_spawns]
    assert roles.count("chief") == 1, "orc_vol needs exactly one chief spawn"
    assert roles.count("shaman") == 1, "orc_vol needs exactly one shaman spawn"


def test_orc_dec_tribe_has_exactly_one_chief_and_one_shaman() -> None:
    dec_spawns = [s for s in orc.SPAWNS if s.get("is_leader") and s["room"].startswith("orc_dec")]
    roles = [s.get("leader_role") for s in dec_spawns]
    assert roles.count("chief") == 1, "orc_dec needs exactly one chief spawn"
    assert roles.count("shaman") == 1, "orc_dec needs exactly one shaman spawn"


def test_orc_leader_spawns_are_single() -> None:
    for spawn in orc.SPAWNS:
        if spawn.get("is_leader"):
            assert spawn.get("leader_role") in {"chief", "shaman"}
            assert spawn["count"] == 1, "a leader spawn must be count=1"


# ---------------------------------------------------------------------------
# Group 5 — War rivalry config (pure)
# ---------------------------------------------------------------------------


def test_orc_vol_orc_dec_initial_tension_is_war() -> None:
    """The faction config encodes the orc blood feud at war-band tension (+24)."""
    pair = frozenset({"orc_vol", "orc_dec"})
    tension = INITIAL_RELATIONS[pair]
    assert band_for(tension, RELATION_LADDER) == "war"


def test_orc_vol_designated_rival_is_orc_dec() -> None:
    assert repop_cfg.DESIGNATED_RIVAL["orc_vol"] == "orc_dec"


def test_orc_dec_designated_rival_is_orc_vol() -> None:
    assert repop_cfg.DESIGNATED_RIVAL["orc_dec"] == "orc_vol"


# ---------------------------------------------------------------------------
# Group 6 — Spawn-point derivation (pure, no Evennia)
# ---------------------------------------------------------------------------


def test_orc_spawn_points_expand_count() -> None:
    points = spawn_points("caves", orc.SPAWNS, orc.MOB_TEMPLATES)
    assert len(points) == sum(s["count"] for s in orc.SPAWNS)


def test_orc_spawn_point_ids_unique() -> None:
    points = spawn_points("caves", orc.SPAWNS, orc.MOB_TEMPLATES)
    ids = [p.spawn_id for p in points]
    assert len(ids) == len(set(ids))


def test_orc_vol_derived_leaders() -> None:
    points = spawn_points("caves", orc.SPAWNS, orc.MOB_TEMPLATES)
    vol_leaders = [p for p in points if p.is_leader and p.faction == "orc_vol"]
    roles = [p.leader_role for p in vol_leaders]
    assert roles.count("chief") == 1
    assert roles.count("shaman") == 1


def test_orc_dec_derived_leaders() -> None:
    points = spawn_points("caves", orc.SPAWNS, orc.MOB_TEMPLATES)
    dec_leaders = [p for p in points if p.is_leader and p.faction == "orc_dec"]
    roles = [p.leader_role for p in dec_leaders]
    assert roles.count("chief") == 1
    assert roles.count("shaman") == 1


def test_orc_spawn_point_rooms_are_zone_namespaced() -> None:
    for point in spawn_points("caves", orc.SPAWNS, orc.MOB_TEMPLATES):
        assert point.room.startswith("caves:")


# ---------------------------------------------------------------------------
# Engine fixtures
# ---------------------------------------------------------------------------


def _caves_rooms() -> list[Any]:
    from evennia.utils.search import search_object_by_tag  # noqa: PLC0415

    from world.zones.builder import ROOM_CATEGORY  # noqa: PLC0415

    return [r for r in search_object_by_tag(category=ROOM_CATEGORY) if r.db.zone == "caves"]


def _caves_exits() -> list[Any]:
    from evennia.utils.search import search_object_by_tag  # noqa: PLC0415

    from world.zones.builder import EXIT_CATEGORY  # noqa: PLC0415

    out = []
    for e in search_object_by_tag(category=EXIT_CATEGORY):
        loc = e.location
        if loc is not None and loc.db.zone == "caves":
            out.append(e)
    return out


def _find_caves_room(room_key: str) -> Any:
    from evennia.utils.search import search_object_by_tag  # noqa: PLC0415

    from world.zones.builder import ROOM_CATEGORY  # noqa: PLC0415

    matches = search_object_by_tag(f"caves:{room_key}", category=ROOM_CATEGORY)
    return matches[0] if matches else None


@pytest.fixture
def built_caves() -> Iterator[None]:
    """Build the caves zone (hub + all discovered tribes), yield, tear down."""
    caves.build()
    try:
        yield
    finally:
        for exit_ in _caves_exits():
            exit_.delete()
        for room in _caves_rooms():
            room.delete()


@pytest.fixture
def repop_and_factions() -> Iterator[tuple[Any, Any]]:
    """A registered repop_manager + faction_manager, torn down after the test."""
    from evennia.utils import create  # noqa: PLC0415

    all_spawns = caves.SPAWNS
    all_mobs = caves.MOB_TEMPLATES
    repop = create.create_script("world.managers.repop_manager.RepopManager")
    factions = create.create_script("world.managers.faction_manager.FactionManager")
    repop.register_zone("caves", all_spawns, all_mobs)
    try:
        yield repop, factions
    finally:
        repop.delete()
        factions.delete()


# ---------------------------------------------------------------------------
# Engine tests — build() materialises the orc lairs
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_build_creates_orc_vol_rooms(built_caves: None) -> None:
    built = {r.db.room_key for r in _caves_rooms()}
    assert built >= ORC_VOL_ROOMS, f"missing: {ORC_VOL_ROOMS - built}"


@pytest.mark.django_db
def test_build_creates_orc_dec_rooms(built_caves: None) -> None:
    built = {r.db.room_key for r in _caves_rooms()}
    assert built >= ORC_DEC_ROOMS, f"missing: {ORC_DEC_ROOMS - built}"


@pytest.mark.django_db
def test_orc_vol_lair_rooms_have_dark_flag(built_caves: None) -> None:
    from world.zones.builder import FLAG_CATEGORY  # noqa: PLC0415

    chief = _find_caves_room("orc_vol_chief")
    assert chief is not None
    assert chief.tags.has("dark", category=FLAG_CATEGORY)


@pytest.mark.django_db
def test_orc_dec_lair_rooms_have_dark_flag(built_caves: None) -> None:
    from world.zones.builder import FLAG_CATEGORY  # noqa: PLC0415

    chief = _find_caves_room("orc_dec_chief")
    assert chief is not None
    assert chief.tags.has("dark", category=FLAG_CATEGORY)


@pytest.mark.django_db
def test_ravine_north_exits_to_both_orc_mouths(built_caves: None) -> None:
    ravine_north = _find_caves_room("ravine_north")
    assert ravine_north is not None
    dest_keys = {e.destination.db.room_key for e in ravine_north.exits if e.destination}
    assert "orc_vol_mouth" in dest_keys, "ravine_north has no exit into orc_vol lair"
    assert "orc_dec_mouth" in dest_keys, "ravine_north has no exit into orc_dec lair"


@pytest.mark.django_db
def test_orc_internal_exits_are_reversible(built_caves: None) -> None:
    mouth = _find_caves_room("orc_vol_mouth")
    guard = _find_caves_room("orc_vol_guard")
    assert mouth is not None and guard is not None
    north = [e for e in mouth.exits if e.key == "n"]
    assert north and north[0].destination == guard
    south = [e for e in guard.exits if e.key == "s"]
    assert south and south[0].destination == mouth


# ---------------------------------------------------------------------------
# Engine tests — orc_vol leadership halt + orc_dec rival scouting
# ---------------------------------------------------------------------------


def _orc_vol_leaders() -> tuple[Any, Any]:
    points = spawn_points("caves", caves.SPAWNS, caves.MOB_TEMPLATES)
    chief = next(p for p in points if p.leader_role == "chief" and p.faction == "orc_vol")
    shaman = next(p for p in points if p.leader_role == "shaman" and p.faction == "orc_vol")
    return chief, shaman


def _orc_dec_leaders() -> tuple[Any, Any]:
    points = spawn_points("caves", caves.SPAWNS, caves.MOB_TEMPLATES)
    chief = next(p for p in points if p.leader_role == "chief" and p.faction == "orc_dec")
    shaman = next(p for p in points if p.leader_role == "shaman" and p.faction == "orc_dec")
    return chief, shaman


def _make_leader_mob(spawn_id: str, key: str, faction: str, room: Any) -> Any:
    from evennia.utils import create  # noqa: PLC0415

    mob = create.create_object("typeclasses.npcs.Mob", key=key, location=room)
    mob.db.spawn_id = spawn_id
    mob.db.faction_id = faction
    return mob


@pytest.mark.django_db
def test_killing_one_orc_vol_leader_does_not_halt(repop_and_factions: tuple[Any, Any]) -> None:
    from evennia.utils import create  # noqa: PLC0415

    repop, _ = repop_and_factions
    chief, _shaman = _orc_vol_leaders()
    room = create.create_object("typeclasses.rooms.Room", key="orc-halt-room-vol-1")
    try:
        chief_mob = _make_leader_mob(chief.spawn_id, "Grukk", "orc_vol", room)
        chief_mob.at_death()
        assert chief.spawn_id in (repop.db.respawn_at or {})
        assert "orc_vol" not in (repop.db.halted_until or {})
        assert not (repop.db.scouts or {})
    finally:
        room.delete()


@pytest.mark.django_db
def test_killing_both_orc_vol_leaders_halts_and_dec_scouts(
    repop_and_factions: tuple[Any, Any],
) -> None:
    """Vile Rune chief + shaman down → tribe frozen, Decapitators scout the lair."""
    from evennia.utils import create  # noqa: PLC0415

    repop, factions = repop_and_factions
    chief, shaman = _orc_vol_leaders()
    baseline = factions.get_tension("orc_vol", "orc_dec")
    room = create.create_object("typeclasses.rooms.Room", key="orc-halt-room-vol-2")
    try:
        chief_mob = _make_leader_mob(chief.spawn_id, "Grukk", "orc_vol", room)
        shaman_mob = _make_leader_mob(shaman.spawn_id, "Mawg", "orc_vol", room)
        chief_mob.at_death()
        shaman_mob.at_death()

        halted_until = (repop.db.halted_until or {}).get("orc_vol")
        assert halted_until is not None and halted_until > time.time()

        scouts = repop.db.scouts or {}
        assert len(scouts) == repop_cfg.SCOUT_PARTY_SIZE
        assert all(s["faction"] == "orc_dec" for s in scouts.values())
        assert all(s["scouting"] == "orc_vol" for s in scouts.values())

        assert factions.get_tension("orc_vol", "orc_dec") > baseline
    finally:
        room.delete()


@pytest.mark.django_db
def test_killing_both_orc_dec_leaders_halts_and_vol_scouts(
    repop_and_factions: tuple[Any, Any],
) -> None:
    """Decapitator chief + shaman down → tribe frozen, Vile Rune scouts the lair."""
    from evennia.utils import create  # noqa: PLC0415

    repop, factions = repop_and_factions
    chief, shaman = _orc_dec_leaders()
    baseline = factions.get_tension("orc_vol", "orc_dec")
    room = create.create_object("typeclasses.rooms.Room", key="orc-halt-room-dec-1")
    try:
        chief_mob = _make_leader_mob(chief.spawn_id, "Bloodtusk", "orc_dec", room)
        shaman_mob = _make_leader_mob(shaman.spawn_id, "Ssruk", "orc_dec", room)
        chief_mob.at_death()
        shaman_mob.at_death()

        halted_until = (repop.db.halted_until or {}).get("orc_dec")
        assert halted_until is not None and halted_until > time.time()

        scouts = repop.db.scouts or {}
        assert len(scouts) == repop_cfg.SCOUT_PARTY_SIZE
        assert all(s["faction"] == "orc_vol" for s in scouts.values())
        assert all(s["scouting"] == "orc_dec" for s in scouts.values())

        assert factions.get_tension("orc_vol", "orc_dec") > baseline
    finally:
        room.delete()


# ---------------------------------------------------------------------------
# Engine tests — faction standing shifts observable in orc behavior
# ---------------------------------------------------------------------------


def _teardown_room(room: Any, *characters: Any) -> None:
    for obj in list(room.contents):
        if obj.pk is not None:
            obj.delete()
    room.delete()
    for char in characters:
        if char.pk is not None:
            char.delete()


def _make_orc_mob(
    room: Any, faction: str, key: str = "orc-grunt", *, is_leader: bool = False
) -> Any:
    from evennia.utils import create  # noqa: PLC0415

    mob = create.create_object("typeclasses.npcs.Mob", key=key, location=room)
    mob.db.faction_id = faction
    mob.db.is_leader = is_leader
    return mob


@pytest.mark.django_db
def test_killing_orc_vol_member_lowers_player_standing(
    repop_and_factions: tuple[Any, Any],
) -> None:
    from world.factions.config import STANDING_EVENTS  # noqa: PLC0415

    _, factions = repop_and_factions
    from evennia.utils import create  # noqa: PLC0415

    room = create.create_object("typeclasses.rooms.Room", key="orc-standing-room-1")
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="orc-vol-slayer")
    try:
        assert factions.get_standing("orc_vol", str(char.id)) == 0
        mob = _make_orc_mob(room, "orc_vol")
        mob.db.last_attacker = char
        mob.at_death()
        assert factions.get_standing("orc_vol", str(char.id)) == STANDING_EVENTS["kill_member"]
    finally:
        _teardown_room(room, char)


@pytest.mark.django_db
def test_killing_orc_dec_member_lowers_player_standing(
    repop_and_factions: tuple[Any, Any],
) -> None:
    from world.factions.config import STANDING_EVENTS  # noqa: PLC0415

    _, factions = repop_and_factions
    from evennia.utils import create  # noqa: PLC0415

    room = create.create_object("typeclasses.rooms.Room", key="orc-standing-room-2")
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="orc-dec-slayer")
    try:
        assert factions.get_standing("orc_dec", str(char.id)) == 0
        mob = _make_orc_mob(room, "orc_dec")
        mob.db.last_attacker = char
        mob.at_death()
        assert factions.get_standing("orc_dec", str(char.id)) == STANDING_EVENTS["kill_member"]
    finally:
        _teardown_room(room, char)


@pytest.mark.django_db
def test_killing_orc_leader_lowers_standing_more(
    repop_and_factions: tuple[Any, Any],
) -> None:
    from world.factions.config import STANDING_EVENTS  # noqa: PLC0415

    _, factions = repop_and_factions
    from evennia.utils import create  # noqa: PLC0415

    room = create.create_object("typeclasses.rooms.Room", key="orc-standing-room-3")
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="orc-leader-slayer")
    try:
        chief = _make_orc_mob(room, "orc_vol", key="Grukk", is_leader=True)
        chief.db.last_attacker = char
        chief.at_death()
        assert factions.get_standing("orc_vol", str(char.id)) == STANDING_EVENTS["kill_leader"]
    finally:
        _teardown_room(room, char)


@pytest.mark.django_db
def test_orc_vol_kills_drive_to_kos_and_survivor_aggros(
    repop_and_factions: tuple[Any, Any],
) -> None:
    """End-to-end M4↔zone tie: enough orc_vol kills → kill-on-sight; survivor aggros."""
    _, factions = repop_and_factions
    from evennia.utils import create  # noqa: PLC0415

    room = create.create_object("typeclasses.rooms.Room", key="orc-kos-room-vol")
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="orc-vol-scourge")
    try:
        for i in range(10):
            mob = _make_orc_mob(room, "orc_vol", key=f"orc-vol-grunt-{i}")
            mob.db.last_attacker = char
            mob.at_death()
        assert factions.standing_band("orc_vol", str(char.id)) == "kill-on-sight"

        _make_orc_mob(room, "orc_vol", key="orc-vol-sentry-survivor")
        messages: list[str] = []
        char.msg = lambda text, **_kw: messages.append(str(text))
        char.move_to(room, quiet=True)
        assert any("attacks" in m.lower() for m in messages)
    finally:
        _teardown_room(room, char)
