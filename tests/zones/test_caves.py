"""Caves of Chaos zone tests — M9 kobold slice.

Derived from docs/specs/zones.md §6 and docs/specs/zones/caves.md. Pure-data
groups validate the static room/exit/mob/spawn data without booting Evennia;
the engine groups (pytest-django) verify build() materialises and links the
zone.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest

from world.factions.config import FACTIONS
from world.zones import caves
from world.zones.caves.exits import EXITS
from world.zones.caves.mobs import MOB_TEMPLATES
from world.zones.caves.rooms import ROOMS
from world.zones.caves.spawns import SPAWNS

# Rooms that are part of a (dark) lair vs the open-air ravine spine.
RAVINE_ROOMS: frozenset[str] = frozenset({"ravine", "ravine_north", "ravine_mid", "ravine_south"})
KOBOLD_LAIR_ROOMS: frozenset[str] = frozenset(
    {
        "kobold_mouth",
        "kobold_guard",
        "kobold_kennels",
        "kobold_warren",
        "kobold_grotto",
        "kobold_den",
    }
)


# ---------------------------------------------------------------------------
# Group 1 — Standard zone interface
# ---------------------------------------------------------------------------


def test_zone_exposes_standard_interface() -> None:
    assert callable(caves.build)
    assert isinstance(caves.ROOMS, list)
    assert isinstance(caves.EXITS, list)
    assert isinstance(caves.MOB_TEMPLATES, list)
    assert isinstance(caves.SPAWNS, list)
    assert isinstance(caves.NPCS, list)
    assert caves.ZONE == "caves"


# ---------------------------------------------------------------------------
# Group 2 — Room / exit data integrity (zones spec §6: 2, 8)
# ---------------------------------------------------------------------------


def test_room_keys_unique() -> None:
    keys = [r["key"] for r in ROOMS]
    assert len(keys) == len(set(keys)), "duplicate room key in caves ROOMS"


def test_expected_rooms_present() -> None:
    keys = {r["key"] for r in ROOMS}
    assert keys >= RAVINE_ROOMS
    assert keys >= KOBOLD_LAIR_ROOMS


def test_no_dangling_intra_zone_exits() -> None:
    room_keys = {r["key"] for r in ROOMS}
    for exit_ in EXITS:
        assert exit_["from"] in room_keys, f"exit from unknown room {exit_['from']!r}"
        to = exit_["to"]
        if ":" in to:
            continue  # inter-zone target, validated separately
        assert to in room_keys, f"exit to unknown room {to!r}"


def test_inter_zone_exit_targets_wilderness_ravine_mouth() -> None:
    inter = [e for e in EXITS if ":" in e["to"]]
    assert inter, "caves should expose an inter-zone exit to the wilderness"
    assert any(e["to"] == "wilderness:ravine_mouth" for e in inter)


def test_lair_rooms_are_dark() -> None:
    by_key = {r["key"]: r for r in ROOMS}
    for key in KOBOLD_LAIR_ROOMS:
        assert by_key[key].get("dark") is True, f"{key} should be dark"


def test_ravine_rooms_are_lit() -> None:
    by_key = {r["key"]: r for r in ROOMS}
    for key in RAVINE_ROOMS:
        assert not by_key[key].get("dark"), f"open-air {key} should not be dark"


# ---------------------------------------------------------------------------
# Group 3 — Mob templates (zones spec §6: 3, 9)
# ---------------------------------------------------------------------------


def test_mob_factions_are_valid_ids() -> None:
    valid = set(FACTIONS.keys())
    for mob in MOB_TEMPLATES:
        assert mob["faction"] in valid, f"mob {mob['key']!r} bad faction {mob['faction']!r}"


def test_kobold_mobs_use_kobold_faction() -> None:
    assert all(m["faction"] == "kobold" for m in MOB_TEMPLATES)


def test_mob_ascending_ac_in_range() -> None:
    for mob in MOB_TEMPLATES:
        assert mob["ac"] >= 10, f"mob {mob['key']!r} AC {mob['ac']} below ascending base 10"


def test_mob_keys_unique() -> None:
    keys = [m["key"] for m in MOB_TEMPLATES]
    assert len(keys) == len(set(keys))


# ---------------------------------------------------------------------------
# Group 4 — Spawns + leadership (zones spec §6: 4, 5)
# ---------------------------------------------------------------------------


def test_spawn_templates_are_defined() -> None:
    mob_keys = {m["key"] for m in MOB_TEMPLATES}
    for spawn in SPAWNS:
        assert spawn["template"] in mob_keys, (
            f"spawn in {spawn['room']!r} references unknown template {spawn['template']!r}"
        )


def test_spawn_rooms_exist() -> None:
    room_keys = {r["key"] for r in ROOMS}
    for spawn in SPAWNS:
        assert spawn["room"] in room_keys, f"spawn references unknown room {spawn['room']!r}"


def test_kobold_tribe_has_exactly_one_chief_and_one_shaman() -> None:
    roles = [s.get("leader_role") for s in SPAWNS if s.get("is_leader")]
    assert roles.count("chief") == 1, "kobold tribe needs exactly one chief spawn"
    assert roles.count("shaman") == 1, "kobold tribe needs exactly one shaman spawn"


def test_leader_spawns_are_single_and_well_formed() -> None:
    for spawn in SPAWNS:
        if spawn.get("is_leader"):
            assert spawn.get("leader_role") in {"chief", "shaman"}
            assert spawn["count"] == 1, "a leader spawn must be a single mob"


# ---------------------------------------------------------------------------
# Engine tests (require Django) — build() materialises and links the zone
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
    """Build the caves alone (no wilderness), yield, then tear them down."""
    caves.build()
    try:
        yield
    finally:
        for exit_ in _caves_exits():
            exit_.delete()
        for room in _caves_rooms():
            room.delete()


@pytest.fixture
def built_wilderness_and_caves() -> Iterator[None]:
    """Build the Wilderness then the caves, yield, then tear both down."""
    from evennia.utils.search import search_object_by_tag  # noqa: PLC0415

    from world.zones import wilderness  # noqa: PLC0415
    from world.zones.builder import EXIT_CATEGORY, NPC_CATEGORY  # noqa: PLC0415

    wilderness.build()
    caves.build()
    try:
        yield
    finally:
        from evennia.contrib.grid.xyzgrid.xyzgrid import get_xyzgrid  # noqa: PLC0415

        # caves exits (incl. the return exit) and the forward 'enter' exit first.
        for exit_ in _caves_exits():
            exit_.delete()
        for exit_ in search_object_by_tag("wilderness:ravine_mouth:enter", category=EXIT_CATEGORY):
            exit_.delete()
        # Wilderness NPCs (the hermit) before remove_map (their home is a grid room).
        for npc in search_object_by_tag(category=NPC_CATEGORY):
            npc.delete()
        get_xyzgrid().remove_map("wilderness", remove_objects=True)
        for room in _caves_rooms():
            room.delete()


@pytest.mark.django_db
def test_build_creates_every_room(built_caves: None) -> None:
    built = {r.db.room_key for r in _caves_rooms()}
    assert built == {r["key"] for r in ROOMS}


@pytest.mark.django_db
def test_build_is_idempotent(built_caves: None) -> None:
    first_rooms = {r.id for r in _caves_rooms()}
    first_exits = {e.id for e in _caves_exits()}
    caves.build()
    assert {r.id for r in _caves_rooms()} == first_rooms
    assert {e.id for e in _caves_exits()} == first_exits


@pytest.mark.django_db
def test_lair_rooms_get_dark_flag(built_caves: None) -> None:
    from world.zones.builder import FLAG_CATEGORY  # noqa: PLC0415

    den = _find_caves_room("kobold_den")
    assert den is not None
    assert den.tags.has("dark", category=FLAG_CATEGORY)

    ravine = _find_caves_room("ravine")
    assert ravine is not None
    assert not ravine.tags.has("dark", category=FLAG_CATEGORY)


@pytest.mark.django_db
def test_ravine_tagged_as_wilderness_target(built_caves: None) -> None:
    """The ravine floor carries the caves:ravine_mouth alias the wilderness uses."""
    from evennia.utils.search import search_object_by_tag  # noqa: PLC0415

    from world.zones.builder import ROOM_CATEGORY  # noqa: PLC0415

    matches = search_object_by_tag("caves:ravine_mouth", category=ROOM_CATEGORY)
    assert len(matches) == 1
    assert matches[0].db.room_key == "ravine"


@pytest.mark.django_db
def test_internal_exit_is_reversible(built_caves: None) -> None:
    mouth = _find_caves_room("kobold_mouth")
    guard = _find_caves_room("kobold_guard")
    north = [e for e in mouth.exits if e.key == "n"]
    assert north and north[0].destination == guard
    south = [e for e in guard.exits if e.key == "s"]
    assert south and south[0].destination == mouth


@pytest.mark.django_db
def test_wilderness_to_caves_round_trip(built_wilderness_and_caves: None) -> None:
    """The ravine mouth links both ways: wilderness -> caves and back."""
    from evennia.utils.search import search_object_by_tag  # noqa: PLC0415

    from world.zones.builder import ROOM_CATEGORY  # noqa: PLC0415

    mouth_matches = search_object_by_tag("wilderness:ravine_mouth", category=ROOM_CATEGORY)
    assert mouth_matches
    mouth = mouth_matches[0]
    ravine = _find_caves_room("ravine")
    assert ravine is not None

    # Forward: wilderness ravine mouth -> caves ravine via 'enter'.
    enter = [e for e in mouth.exits if e.key == "enter"]
    assert enter, "no 'enter' exit from wilderness ravine_mouth into the caves"
    assert enter[0].destination == ravine

    # Return: caves ravine -> wilderness ravine mouth via 'w'.
    back = [e for e in ravine.exits if e.key == "w"]
    assert back, "no return exit from the caves ravine to the wilderness"
    assert back[0].destination == mouth
