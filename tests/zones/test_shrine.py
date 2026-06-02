"""Pure-data validation for the Shrine zone (zones spec docs/specs/zones/shrine.md).

These tests boot no Evennia: they validate the static room/exit data only —
the ~16-room temple layout, the dark/no_recall flag table, intra-zone
connectivity, and the single inter-zone link back to the Caves minotaur maze.
Build-time behaviour (idempotency, reset, season-end) lives in later slices.
"""

from __future__ import annotations

from world.zones import shrine
from world.zones.records import ExitRecord, RoomRecord
from world.zones.shrine.exits import REVERSE

EXPECTED_ROOMS = {
    "shrine_gate",
    "narthex",
    "nave_evil",
    "side_chapel_n",
    "side_chapel_s",
    "crypt_upper",
    "crypt_lower",
    "cells",
    "acolyte_dorm",
    "adept_study",
    "river_cavern",
    "ritual_hall",
    "inner_sanctum",
    "altar_of_chaos",
    "boss_lair",
    "secret_vault",
}

# Per the spec flag table: every room below the threshold (gate + narthex)
# requires light; the deep rooms additionally forbid recall.
EXPECTED_DARK = EXPECTED_ROOMS - {"shrine_gate", "narthex"}
EXPECTED_NO_RECALL = {
    "crypt_lower",
    "river_cavern",
    "ritual_hall",
    "inner_sanctum",
    "altar_of_chaos",
    "boss_lair",
    "secret_vault",
}


def _room_keys() -> set[str]:
    return {r["key"] for r in shrine.ROOMS}


def _by_key() -> dict[str, RoomRecord]:
    return {r["key"]: r for r in shrine.ROOMS}


def _intra_exits() -> list[ExitRecord]:
    """Exits whose target is inside the Shrine (no ``zone:`` prefix)."""
    return [e for e in shrine.EXITS if ":" not in e["to"]]


def test_zone_exposes_standard_interface() -> None:
    """The zone exposes build() and the standard data lists."""
    assert callable(shrine.build)
    assert isinstance(shrine.ROOMS, list)
    assert isinstance(shrine.EXITS, list)
    assert isinstance(shrine.MOB_TEMPLATES, list)
    assert isinstance(shrine.SPAWNS, list)
    assert isinstance(shrine.NPCS, list)


def test_room_set_matches_spec() -> None:
    """The Shrine defines exactly the ~16 rooms from the outline."""
    assert _room_keys() == EXPECTED_ROOMS


def test_room_keys_unique() -> None:
    """No two rooms share a key."""
    keys = [r["key"] for r in shrine.ROOMS]
    assert len(keys) == len(set(keys))


def test_every_room_has_name_and_desc() -> None:
    """Each room carries non-empty name/desc and the shrine zone id."""
    for room in shrine.ROOMS:
        assert room["zone"] == "shrine"
        assert room["name"].strip()
        assert room["desc"].strip()


def test_no_dangling_intra_zone_exits() -> None:
    """Every intra-Shrine exit from/to resolves to a real room."""
    keys = _room_keys()
    for exit_ in _intra_exits():
        assert exit_["from"] in keys
        assert exit_["to"] in keys


def test_exit_directions_unique_per_room() -> None:
    """No room has two exits in the same direction."""
    seen: set[tuple[str, str]] = set()
    for exit_ in shrine.EXITS:
        ident = (exit_["from"], exit_["dir"])
        assert ident not in seen, f"duplicate exit {ident}"
        seen.add(ident)


def test_intra_exits_are_reversible() -> None:
    """Every intra-Shrine passage can be walked both ways."""
    pairs = {(e["from"], e["dir"], e["to"]) for e in _intra_exits()}
    for src, direction, dst in pairs:
        assert (dst, REVERSE[direction], src) in pairs, f"no reverse for {src} {direction} {dst}"


def test_all_rooms_reachable_from_gate() -> None:
    """The room graph is connected: every room is reachable from the Black Gate."""
    adjacency: dict[str, list[str]] = {k: [] for k in _room_keys()}
    for exit_ in _intra_exits():
        adjacency[exit_["from"]].append(exit_["to"])
    seen = {"shrine_gate"}
    stack = ["shrine_gate"]
    while stack:
        node = stack.pop()
        for nxt in adjacency[node]:
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    assert seen == _room_keys()


def test_dark_flags_match_spec() -> None:
    """Exactly the rooms below the threshold carry the ``dark`` flag."""
    rooms = _by_key()
    dark = {key for key, room in rooms.items() if room.get("dark")}
    assert dark == EXPECTED_DARK


def test_no_recall_flags_match_spec() -> None:
    """Exactly the deep rooms carry ``no_recall`` (climax stays committed)."""
    rooms = _by_key()
    no_recall = {key for key, room in rooms.items() if room.get("no_recall")}
    assert no_recall == EXPECTED_NO_RECALL


def test_no_recall_rooms_are_also_dark() -> None:
    """Every no_recall deep room is also dark — they sit below the threshold."""
    rooms = _by_key()
    for key in EXPECTED_NO_RECALL:
        assert rooms[key].get("dark"), f"{key} is no_recall but not dark"


def test_threshold_rooms_allow_recall() -> None:
    """The gate and narthex are not no_recall — players can still recall there."""
    rooms = _by_key()
    assert not rooms["shrine_gate"].get("no_recall")
    assert not rooms["narthex"].get("no_recall")


def test_shrine_gate_links_back_to_minotaur_maze() -> None:
    """Exactly one inter-zone exit leaves the Shrine: gate -> minotaur maze.

    The Caves minotaur maze descends ``d`` to ``shrine:shrine_gate``; this is
    the reverse, ``u`` back to the maze's deep passage.
    """
    interzone = [e for e in shrine.EXITS if ":" in e["to"]]
    assert len(interzone) == 1
    exit_ = interzone[0]
    assert exit_["from"] == "shrine_gate"
    assert exit_["to"] == "caves:minotaur_shrine_passage"
    assert exit_["dir"] == "u"
