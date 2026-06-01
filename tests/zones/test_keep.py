"""Pure-data validation for the Keep zone (zones spec §6, Keep outline).

These tests boot no Evennia: they validate the static room/exit data only.
Build-time behaviour (idempotency, recall tagging, traversal) lives in
test_keep_build.py.
"""

from __future__ import annotations

from world.zones import keep
from world.zones.keep.exits import REVERSE
from world.zones.records import ExitRecord

EXPECTED_ROOMS = {
    "main_gate",
    "gatehouse",
    "entry_yard",
    "east_wall",
    "west_wall",
    "outer_bailey",
    "provisioner",
    "armorer",
    "weaponsmith",
    "trader",
    "bank",
    "tavern",
    "inn",
    "guild",
    "chapel_nave",
    "chapel_vestry",
    "chapel_bell",
    "fountain_sq",
    "smith_yard",
    "stables",
    "warehouse",
    "bailiff",
    "inner_gate",
    "inner_bailey",
    "audience",
    "keep_tower",
}


def _room_keys() -> set[str]:
    return {r["key"] for r in keep.ROOMS}


def _intra_exits() -> list[ExitRecord]:
    """Exits whose target is inside the Keep (no ``zone:`` prefix)."""
    return [e for e in keep.EXITS if ":" not in e["to"]]


def test_zone_exposes_standard_interface() -> None:
    """The zone exposes build() and the standard data lists."""
    assert callable(keep.build)
    assert isinstance(keep.ROOMS, list)
    assert isinstance(keep.EXITS, list)
    assert isinstance(keep.MOB_TEMPLATES, list)
    assert isinstance(keep.SPAWNS, list)
    assert isinstance(keep.NPCS, list)


def test_keep_has_no_hostile_mobs() -> None:
    """The Keep ships no mobs or spawns in v1."""
    assert keep.MOB_TEMPLATES == []
    assert keep.SPAWNS == []


def test_room_set_matches_spec() -> None:
    """The Keep defines exactly the ~26 rooms from the outline."""
    assert _room_keys() == EXPECTED_ROOMS


def test_room_keys_unique() -> None:
    """No two rooms share a key."""
    keys = [r["key"] for r in keep.ROOMS]
    assert len(keys) == len(set(keys))


def test_every_room_has_name_and_desc() -> None:
    """Each room carries non-empty name/desc and the keep zone id."""
    for room in keep.ROOMS:
        assert room["zone"] == "keep"
        assert room["name"].strip()
        assert room["desc"].strip()


def test_no_dangling_intra_zone_exits() -> None:
    """Every intra-Keep exit from/to resolves to a real room."""
    keys = _room_keys()
    for exit_ in _intra_exits():
        assert exit_["from"] in keys
        assert exit_["to"] in keys


def test_exit_directions_unique_per_room() -> None:
    """No room has two exits in the same direction."""
    seen: set[tuple[str, str]] = set()
    for exit_ in keep.EXITS:
        ident = (exit_["from"], exit_["dir"])
        assert ident not in seen, f"duplicate exit {ident}"
        seen.add(ident)


def test_intra_exits_are_reversible() -> None:
    """Every intra-Keep passage can be walked both ways."""
    pairs = {(e["from"], e["dir"], e["to"]) for e in _intra_exits()}
    for src, direction, dst in pairs:
        assert (dst, REVERSE[direction], src) in pairs, f"no reverse for {src} {direction} {dst}"


def test_all_rooms_reachable_from_main_gate() -> None:
    """The room graph is connected: every room is reachable from the gate."""
    adjacency: dict[str, list[str]] = {k: [] for k in _room_keys()}
    for exit_ in _intra_exits():
        adjacency[exit_["from"]].append(exit_["to"])
    seen = {"main_gate"}
    stack = ["main_gate"]
    while stack:
        node = stack.pop()
        for nxt in adjacency[node]:
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    assert seen == _room_keys()


def test_inner_bailey_is_recall_room() -> None:
    """The recall point — the Inner Bailey — exists in the Keep."""
    assert "inner_bailey" in _room_keys()


def test_main_gate_opens_onto_wilderness() -> None:
    """Exactly one inter-zone exit leaves the Keep: gate -> wilderness."""
    interzone = [e for e in keep.EXITS if ":" in e["to"]]
    assert len(interzone) == 1
    assert interzone[0]["from"] == "main_gate"
    assert interzone[0]["to"] == "wilderness:keep_road"
