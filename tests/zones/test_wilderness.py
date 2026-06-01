"""Wilderness zone tests (wilderness spec §11).

Groups 1-3 and 6 are pure-data (no Django/Evennia boot).
Groups 4-5 are engine tests requiring pytest-django.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest

from world.factions.config import FACTIONS
from world.zones import wilderness
from world.zones.wilderness.mobs import ENCOUNTER_TABLE, MOB_TEMPLATES
from world.zones.wilderness.spawns import SPAWNS
from world.zones.wilderness.xymap import MAPSTR, PROTOTYPES, XYMAP_DATA

# ---------------------------------------------------------------------------
# Coordinate table (spec §2): room_key -> (xyzgrid_x, xyzgrid_y)
# ---------------------------------------------------------------------------
COORD_TABLE: dict[str, tuple[int, int]] = {
    "keep_road": (0, 1),
    "crossroads": (1, 1),
    "farmlands": (1, 2),
    "river_ford": (2, 1),
    "marsh_edge": (2, 2),
    "swamp": (2, 3),
    "woods_west": (1, 3),
    "woods_deep": (1, 4),
    "hermit_hut": (3, 2),
    "hills_low": (3, 1),
    "hills_high": (3, 0),
    "raider_camp": (4, 1),
    "old_tower": (4, 2),
    "ravine_approach": (5, 1),
    "ravine_mouth": (5, 2),
    "sealed_cleft": (4, 0),
    "glade": (2, 0),
    "overlook": (4, 3),
}

SAFE_ROOMS: frozenset[str] = frozenset({"keep_road", "glade"})

# Expected connectivity from spec §3 (each frozenset is an unordered pair).
EXPECTED_LINKS: frozenset[frozenset[tuple[int, int]]] = frozenset(
    {
        frozenset({(0, 1), (1, 1)}),  # keep_road - crossroads
        frozenset({(1, 1), (2, 1)}),  # crossroads - river_ford
        frozenset({(2, 1), (3, 1)}),  # river_ford - hills_low
        frozenset({(3, 1), (4, 1)}),  # hills_low - raider_camp
        frozenset({(4, 1), (5, 1)}),  # raider_camp - ravine_approach
        frozenset({(5, 1), (5, 2)}),  # ravine_approach - ravine_mouth
        frozenset({(1, 1), (1, 2)}),  # crossroads - farmlands
        frozenset({(1, 2), (1, 3)}),  # farmlands - woods_west
        frozenset({(1, 3), (1, 4)}),  # woods_west - woods_deep
        frozenset({(1, 2), (2, 2)}),  # farmlands - marsh_edge
        frozenset({(2, 2), (3, 2)}),  # marsh_edge - hermit_hut
        frozenset({(3, 2), (4, 2)}),  # hermit_hut - old_tower
        frozenset({(4, 2), (5, 2)}),  # old_tower - ravine_mouth
        frozenset({(2, 1), (2, 2)}),  # river_ford - marsh_edge
        frozenset({(2, 2), (2, 3)}),  # marsh_edge - swamp
        frozenset({(1, 3), (2, 3)}),  # woods_west - swamp
        frozenset({(3, 1), (3, 2)}),  # hills_low - hermit_hut
        frozenset({(3, 0), (3, 1)}),  # hills_high - hills_low
        frozenset({(4, 1), (4, 2)}),  # raider_camp - old_tower
        frozenset({(4, 0), (4, 1)}),  # sealed_cleft - raider_camp
        frozenset({(4, 2), (4, 3)}),  # old_tower - overlook
        frozenset({(2, 0), (2, 1)}),  # glade - river_ford
        frozenset({(2, 0), (3, 0)}),  # glade - hills_high
        frozenset({(3, 0), (4, 0)}),  # hills_high - sealed_cleft
    }
)


# ---------------------------------------------------------------------------
# §11 Group 1 — Data integrity (pure-data)
# ---------------------------------------------------------------------------


def test_xymap_data_has_zcoord() -> None:
    assert XYMAP_DATA["zcoord"] == "wilderness"


def test_xymap_data_has_nonempty_map() -> None:
    assert XYMAP_DATA["map"].strip()


def test_xymap_data_has_prototypes_dict() -> None:
    assert isinstance(XYMAP_DATA["prototypes"], dict)


def test_all_room_keys_have_prototype_entries() -> None:
    """Every room key in the coordinate table has a specific PROTOTYPES entry."""
    for room_key, coord in COORD_TABLE.items():
        assert coord in PROTOTYPES, f"room_key={room_key!r} coord={coord} missing from PROTOTYPES"


def test_safe_flags_only_on_correct_rooms() -> None:
    """keep_road and glade are the only safe hexes (spec §9.5)."""
    safe_found: set[str] = set()
    for coord, proto in PROTOTYPES.items():
        if not isinstance(coord, tuple) or coord == ("*", "*"):
            continue
        if len(coord) != 2:
            continue
        for attr_name, attr_val in proto.get("attrs", []):
            if attr_name == "safe" and attr_val:
                key_for_coord = {v: k for k, v in COORD_TABLE.items()}.get(coord)  # type: ignore[arg-type]
                if key_for_coord:
                    safe_found.add(key_for_coord)
    assert safe_found == SAFE_ROOMS


# ---------------------------------------------------------------------------
# §11 Group 2 — Encounter table (pure-data)
# ---------------------------------------------------------------------------


def test_encounter_table_mob_keys_defined() -> None:
    mob_keys = {m["key"] for m in MOB_TEMPLATES}
    for _weight, mob_key in ENCOUNTER_TABLE:
        assert mob_key in mob_keys, f"{mob_key!r} in ENCOUNTER_TABLE but not in MOB_TEMPLATES"


def test_encounter_table_weights_positive() -> None:
    for weight, mob_key in ENCOUNTER_TABLE:
        assert weight > 0, f"{mob_key!r} has non-positive weight {weight}"


def test_mob_templates_factions_valid() -> None:
    valid_factions = set(FACTIONS.keys())
    for mob in MOB_TEMPLATES:
        assert mob["faction"] in valid_factions, (
            f"mob {mob['key']!r} has unknown faction {mob['faction']!r}"
        )


# ---------------------------------------------------------------------------
# §11 Group 3 — Spawns (pure-data)
# ---------------------------------------------------------------------------


def test_spawns_templates_defined() -> None:
    mob_keys = {m["key"] for m in MOB_TEMPLATES}
    for spawn in SPAWNS:
        assert spawn["template"] in mob_keys, (
            f"spawn in {spawn['room']!r} references unknown template {spawn['template']!r}"
        )


def test_spawns_no_leader_role() -> None:
    for spawn in SPAWNS:
        assert "leader_role" not in spawn, (
            f"spawn in {spawn['room']!r} has leader_role (wilderness has no leadership halt)"
        )


# ---------------------------------------------------------------------------
# §11 Group 6 — Map connectivity (pure-data MAPSTR parse)
# ---------------------------------------------------------------------------


def _parse_mapstr_links(mapstr: str) -> frozenset[frozenset[tuple[int, int]]]:
    """Extract linked coordinate pairs from an xyzgrid MAPSTR string.

    Format rules (spec §3 / xyzgrid contrib convention):
    - Lines starting with '+' are header/footer: skip.
    - Lines whose first non-whitespace char is a digit are node rows:
      the digit(s) encode y; '#' and 'I' at column 2+2x encode nodes.
      '-' at column 3+2x encodes a horizontal (E-W) link.
    - All other non-blank lines are connector rows: '|' at column 2+2x
      encodes a vertical (N-S) link between the previous and next node rows.
    """
    links: set[frozenset[tuple[int, int]]] = set()
    current_y: int | None = None

    for raw_line in mapstr.split("\n"):
        if not raw_line.strip():
            continue
        if raw_line.lstrip().startswith("+"):
            continue

        # Determine if this is a node row or a connector row.
        # Node rows start with a digit (the y label).
        stripped = raw_line.lstrip(" ")
        if stripped and stripped[0].isdigit():
            # Parse y-label (one or two digits).
            i = 0
            while i < len(stripped) and stripped[i].isdigit():
                i += 1
            y = int(stripped[:i])
            current_y = y
            # After the y-label there is one space; content starts at col 2.
            # Node positions sit at col = 2 + 2*x; H-links at col = 3 + 2*x.
            # Only H-links contribute pairs here; node presence is unused.
            for col_idx, ch in enumerate(raw_line):
                if col_idx >= 3 and (col_idx - 3) % 2 == 0 and ch == "-":
                    x_left = (col_idx - 3) // 2
                    links.add(frozenset({(x_left, y), (x_left + 1, y)}))
        else:
            # Connector row: '|' at col 2+2x links current_y and current_y-1.
            if current_y is None:
                continue
            lower_y = current_y - 1
            upper_y = current_y
            for col_idx in range(len(raw_line)):
                ch = raw_line[col_idx]
                if col_idx >= 2 and (col_idx - 2) % 2 == 0 and ch == "|":
                    x = (col_idx - 2) // 2
                    links.add(frozenset({(x, lower_y), (x, upper_y)}))

    return frozenset(links)


def test_mapstr_contains_all_expected_links() -> None:
    """MAPSTR encodes every link from the connectivity table in spec §3."""
    parsed = _parse_mapstr_links(MAPSTR)
    missing = EXPECTED_LINKS - parsed
    assert not missing, f"MAPSTR missing links: {missing}"


def test_mapstr_has_exactly_18_nodes() -> None:
    """MAPSTR defines exactly 18 room nodes."""
    node_coords: set[tuple[int, int]] = set()
    for raw_line in MAPSTR.split("\n"):
        if not raw_line.strip() or raw_line.lstrip().startswith("+"):
            continue
        stripped = raw_line.lstrip(" ")
        if stripped and stripped[0].isdigit():
            i = 0
            while i < len(stripped) and stripped[i].isdigit():
                i += 1
            y = int(stripped[:i])
            for col_idx, ch in enumerate(raw_line):
                if col_idx >= 2 and (col_idx - 2) % 2 == 0 and ch in ("#", "I"):
                    x = (col_idx - 2) // 2
                    node_coords.add((x, y))
    assert len(node_coords) == 18, f"expected 18 nodes, found {len(node_coords)}: {node_coords}"


# ---------------------------------------------------------------------------
# §11 Group 4 — Build (engine tests, requires Django)
# ---------------------------------------------------------------------------


def _find_wilderness_room(room_key: str) -> Any:
    from evennia.utils.search import search_object_by_tag  # noqa: PLC0415

    from world.zones.builder import ROOM_CATEGORY  # noqa: PLC0415

    matches = search_object_by_tag(f"wilderness:{room_key}", category=ROOM_CATEGORY)
    return matches[0] if matches else None


@pytest.fixture
def built_wilderness() -> Iterator[None]:
    """Build the Wilderness, yield, then remove it from the xyzgrid."""
    wilderness.build()
    try:
        yield
    finally:
        from evennia.contrib.grid.xyzgrid.xyzgrid import get_xyzgrid  # noqa: PLC0415
        from evennia.utils.search import search_object_by_tag  # noqa: PLC0415

        from world.zones.builder import NPC_CATEGORY  # noqa: PLC0415

        # Delete placed NPCs (the Mad Hermit) before removing the grid: their
        # home defaults to a grid room, so leaving them makes remove_map crash
        # when that home room is deleted out from under them.
        for npc in search_object_by_tag(category=NPC_CATEGORY):
            npc.delete()

        grid = get_xyzgrid()
        grid.remove_map("wilderness", remove_objects=True)


@pytest.fixture
def built_keep_and_wilderness() -> Iterator[None]:
    """Build the Keep then the Wilderness, yield, then tear both down."""
    from evennia.utils.search import search_object_by_tag  # noqa: PLC0415

    from world.zones import keep  # noqa: PLC0415
    from world.zones.builder import EXIT_CATEGORY, NPC_CATEGORY, ROOM_CATEGORY  # noqa: PLC0415

    keep.build()
    wilderness.build()
    try:
        yield
    finally:
        from evennia.contrib.grid.xyzgrid.xyzgrid import get_xyzgrid  # noqa: PLC0415

        # NPCs (keep staff + wilderness hermit) first: their home defaults to a
        # grid room, so remove_map would crash on leftover NPCs when that home
        # room is deleted.
        for npc in search_object_by_tag(category=NPC_CATEGORY):
            npc.delete()
        # Remove wilderness next (its exits point into the keep).
        grid = get_xyzgrid()
        grid.remove_map("wilderness", remove_objects=True)
        # Remove remaining keep objects.
        for exit_obj in search_object_by_tag(category=EXIT_CATEGORY):
            exit_obj.delete()
        for room in search_object_by_tag(category=ROOM_CATEGORY):
            room.delete()


@pytest.mark.django_db
def test_build_creates_18_rooms(built_wilderness: None) -> None:
    from evennia.contrib.grid.xyzgrid.xyzroom import XYZRoom  # noqa: PLC0415

    rooms = list(XYZRoom.objects.filter_xyz(("*", "*", "wilderness")))
    assert len(rooms) == 18, f"expected 18 rooms, got {len(rooms)}"


@pytest.mark.django_db
def test_keep_road_is_safe(built_wilderness: None) -> None:
    room = _find_wilderness_room("keep_road")
    assert room is not None, "keep_road room not found"
    assert room.db.safe is True


@pytest.mark.django_db
def test_crossroads_is_not_safe(built_wilderness: None) -> None:
    room = _find_wilderness_room("crossroads")
    assert room is not None, "crossroads room not found"
    assert not room.db.safe


@pytest.mark.django_db
def test_gate_exit_wired_when_keep_exists(built_keep_and_wilderness: None) -> None:
    """keep_road has a 'gate' exit pointing to the Keep's main_gate."""
    keep_road = _find_wilderness_room("keep_road")
    assert keep_road is not None

    gate_exits = [e for e in keep_road.exits if e.key == "gate"]
    assert gate_exits, "no 'gate' exit on keep_road"

    from evennia.utils.search import search_object_by_tag  # noqa: PLC0415

    from world.zones.builder import ROOM_CATEGORY  # noqa: PLC0415

    main_gate_matches = search_object_by_tag("keep:main_gate", category=ROOM_CATEGORY)
    assert main_gate_matches
    assert gate_exits[0].destination == main_gate_matches[0]


# ---------------------------------------------------------------------------
# §11 Group 5 — Encounter mechanics (engine tests)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_encounter_spawns_mob_on_roll_1(built_wilderness: None) -> None:
    """Moving into a non-safe room with encounter roll=1 spawns a mob."""
    from unittest.mock import patch  # noqa: PLC0415

    from evennia import create_object  # noqa: PLC0415

    from typeclasses.characters import PlayerCharacter  # noqa: PLC0415
    from typeclasses.npcs import Mob  # noqa: PLC0415

    crossroads = _find_wilderness_room("crossroads")
    assert crossroads is not None

    char = create_object(PlayerCharacter, key="TestHero")
    try:
        before_count = sum(1 for obj in crossroads.contents if isinstance(obj, Mob))
        with patch("world.zones.wilderness.typeclasses._random.randint", return_value=1):
            char.move_to(crossroads, quiet=True)
        after_count = sum(1 for obj in crossroads.contents if isinstance(obj, Mob))
        assert after_count > before_count, "expected a mob to be spawned"
    finally:
        for mob in list(crossroads.contents):
            if isinstance(mob, Mob):
                mob.delete()
        char.delete()


@pytest.mark.django_db
def test_no_encounter_in_safe_room(built_wilderness: None) -> None:
    """Moving into keep_road (safe) never spawns a mob regardless of roll."""
    from unittest.mock import patch  # noqa: PLC0415

    from evennia import create_object  # noqa: PLC0415

    from typeclasses.characters import PlayerCharacter  # noqa: PLC0415
    from typeclasses.npcs import Mob  # noqa: PLC0415

    keep_road = _find_wilderness_room("keep_road")
    assert keep_road is not None

    char = create_object(PlayerCharacter, key="SafeHero")
    try:
        with patch("world.zones.wilderness.typeclasses._random.randint", return_value=1):
            char.move_to(keep_road, quiet=True)
        mobs = [obj for obj in keep_road.contents if isinstance(obj, Mob)]
        assert not mobs, f"expected no mobs in safe room, found {mobs}"
    finally:
        char.delete()


# ---------------------------------------------------------------------------
# Zone standard interface
# ---------------------------------------------------------------------------


def test_zone_exposes_standard_interface() -> None:
    assert callable(wilderness.build)
    assert isinstance(wilderness.MOB_TEMPLATES, list)
    assert isinstance(wilderness.ENCOUNTER_TABLE, list)
    assert isinstance(wilderness.SPAWNS, list)
    assert isinstance(wilderness.NPCS, list)
    assert isinstance(wilderness.XYMAP_DATA, dict)
