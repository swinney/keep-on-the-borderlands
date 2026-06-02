"""Pure-data validation for the Shrine zone (zones spec docs/specs/zones/shrine.md).

These tests boot no Evennia: they validate the static room/exit/mob data only —
the ~16-room temple layout, the dark/no_recall flag table, intra-zone
connectivity, the single inter-zone link back to the Caves minotaur maze, and
the cult mob roster (the Adept boss + sentries, acolytes, and crypt undead).
Build-time behaviour (idempotency, reset, season-end) lives in later slices.
"""

from __future__ import annotations

from world.factions import config as fac_cfg
from world.repop import config as repop_cfg
from world.zones import shrine
from world.zones.records import ExitRecord, RoomRecord
from world.zones.shrine.exits import REVERSE
from world.zones.spawn_registry import spawn_points

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


# ── Mobs / spawns (the cult roster) ─────────────────────────────────────────


def _mob_keys() -> set[str]:
    return {m["key"] for m in shrine.MOB_TEMPLATES}


def test_every_mob_is_cult_faction() -> None:
    """The whole zone is faction ``cult`` (spec §Mobs/factions)."""
    assert shrine.MOB_TEMPLATES, "the Shrine ships a cult roster from this slice on"
    for mob in shrine.MOB_TEMPLATES:
        assert mob["faction"] == "cult", f"{mob['key']} is not cult"


def test_cult_faction_is_defined_and_at_war_with_the_keep() -> None:
    """The cult faction exists and ``keep ↔ cult`` is a war-band tension (spec)."""
    assert "cult" in fac_cfg.FACTIONS
    pair = frozenset({"keep", "cult"})
    band = fac_cfg.band_for(fac_cfg.INITIAL_RELATIONS[pair], fac_cfg.RELATION_LADDER)
    assert band == "war"


def test_mob_keys_unique() -> None:
    """No two mob templates share a key."""
    keys = [m["key"] for m in shrine.MOB_TEMPLATES]
    assert len(keys) == len(set(keys))


def test_the_adept_is_the_boss() -> None:
    """The Adept is present and is the toughest mob (the standing endgame boss)."""
    by_key = {m["key"]: m for m in shrine.MOB_TEMPLATES}
    assert "the_adept" in by_key
    adept = by_key["the_adept"]
    assert adept["level"] == max(m["level"] for m in shrine.MOB_TEMPLATES)


def test_no_leader_spawns() -> None:
    """The cult resets wholesale on the 24h cycle, not the leadership halt.

    No Shrine spawn is flagged ``is_leader`` — that mechanic is tribe-only
    (chief AND shaman), and the cult has neither, so the halt never fires here.
    """
    for spawn in shrine.SPAWNS:
        assert not spawn.get("is_leader"), f"{spawn['room']} spawns a leader"
        assert spawn.get("leader_role") is None


def test_spawns_reference_real_rooms_and_templates() -> None:
    """Every spawn sits in a real Shrine room and names a real mob template.

    ``spawn_points`` raises KeyError on an unknown template, so a clean
    expansion proves template integrity; we additionally check the rooms.
    """
    room_keys = _room_keys()
    template_keys = _mob_keys()
    for spawn in shrine.SPAWNS:
        assert spawn["room"] in room_keys, f"spawn in unknown room {spawn['room']}"
        assert spawn["template"] in template_keys
    # Does not raise -> every spawn template resolves to a faction.
    points = spawn_points(shrine.ZONE, shrine.SPAWNS, shrine.MOB_TEMPLATES)
    assert len(points) == sum(s["count"] for s in shrine.SPAWNS)
    assert all(p.faction == "cult" for p in points)


def test_the_adept_spawns_in_the_inner_sanctum() -> None:
    """The Adept boss stands in the Inner Sanctum (spec §Mobs/factions)."""
    sanctum = [s for s in shrine.SPAWNS if s["room"] == "inner_sanctum"]
    assert any(s["template"] == "the_adept" for s in sanctum)


def test_undead_haunt_the_crypts() -> None:
    """Skeletons/zombies in the upper crypt, wights in the lower (spec table)."""
    crypt_upper = {s["template"] for s in shrine.SPAWNS if s["room"] == "crypt_upper"}
    crypt_lower = {s["template"] for s in shrine.SPAWNS if s["room"] == "crypt_lower"}
    assert "shrine_skeleton" in crypt_upper or "shrine_zombie" in crypt_upper
    assert "shrine_wight" in crypt_lower


def test_boss_lair_is_unpopulated_until_exposure() -> None:
    """``boss_lair`` holds no spawn in v1 — the exposed priest lands at M12."""
    assert not [s for s in shrine.SPAWNS if s["room"] == "boss_lair"]


def test_shrine_spawns_use_the_24h_reset_cadence() -> None:
    """Shrine spawns respawn on the 24h cycle, not the 15-min standard.

    The wholesale ``_reset_shrine`` path is the real restock; per-mob timers are
    pinned to ``SHRINE_RESET`` so the cult never churns on the tribe cadence.
    """
    for spawn in shrine.SPAWNS:
        assert spawn["respawn_seconds"] == repop_cfg.SHRINE_RESET
