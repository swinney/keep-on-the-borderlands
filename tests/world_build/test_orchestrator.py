"""Tests for the boot orchestrator (world-build spec §4, §13.4-§13.5, §13.10).

``build_all()`` brings the static zone content to life: it ensures the four
global managers, builds every zone in dependency order, registers the spawns of
zones that do not self-register, then runs the initial population pass. These
engine tests assert it produces a populated, idempotent world (§13.4, §13.10) and
that the live leaders it spawns drive the M6 leadership-halt -> rival-scouting
path with **real** scout instances standing in the broken tribe's lair (§13.5).

The full build is heavy (it spawns the xyzgrid Wilderness), so the fixture builds
once per test and tears the world down grid-safely afterward, mirroring
``tests/zones/test_m9_vertical_slice``.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from typing import Any

import pytest
from evennia.utils.search import search_object_by_tag, search_script

from world.build import orchestrator, spawner
from world.zones.builder import EXIT_CATEGORY, NPC_CATEGORY, OBJECT_CATEGORY, ROOM_CATEGORY
from world.zones.caves import MOB_TEMPLATES, SPAWNS
from world.zones.spawn_registry import spawn_points

MANAGER_KEYS = ("faction_manager", "repop_manager", "season_manager", "priest_manager")
SPAWN_CATEGORY = spawner.SPAWN_INSTANCE_CATEGORY


def _spawn_instances() -> list[Any]:
    """Every live object carrying a spawn-instance tag (mobs + scouts)."""
    return list(search_object_by_tag(category=SPAWN_CATEGORY))


def _live(instance_id: str) -> Any:
    """The live instance tagged ``instance_id``, or None."""
    matches = search_object_by_tag(instance_id, category=SPAWN_CATEGORY)
    return matches[0] if matches else None


def _cave_tribes_with_leaders() -> dict[str, dict[str, Any]]:
    """Map each cave faction with both leaders to ``{role: SpawnPoint}``.

    Solitary beasts (the minotaur) have no chief/shaman and are excluded, so the
    R3 leadership halt only ever fires for a tribe that has both.
    """
    by_faction: dict[str, dict[str, Any]] = {}
    for point in spawn_points("caves", SPAWNS, MOB_TEMPLATES):
        if point.leader_role in ("chief", "shaman"):
            by_faction.setdefault(point.faction, {})[point.leader_role] = point
    return {f: roles for f, roles in by_faction.items() if {"chief", "shaman"} <= roles.keys()}


def _teardown_world() -> None:
    """Tear down managers, spawned instances, and all three zones grid-safely."""
    from evennia.contrib.grid.xyzgrid.xyzgrid import get_xyzgrid  # noqa: PLC0415

    # Spawned mobs/scouts first — they sit in rooms about to be deleted.
    for obj in _spawn_instances():
        if obj.pk is not None:
            obj.delete()
    for key in MANAGER_KEYS:
        for mgr in search_script(key):
            mgr.delete()
    # Exits (incl. the grid-attached inter-zone bridges) and NPCs before
    # remove_map deletes the grid rooms they point at.
    for exit_ in search_object_by_tag(category=EXIT_CATEGORY):
        if exit_.pk is not None:
            exit_.delete()
    for npc in search_object_by_tag(category=NPC_CATEGORY):
        if npc.pk is not None:
            npc.delete()
    for obj in search_object_by_tag(category=OBJECT_CATEGORY):
        if obj.pk is not None:
            obj.delete()
    get_xyzgrid().remove_map("wilderness", remove_objects=True)
    for room in search_object_by_tag(category=ROOM_CATEGORY):
        if room.pk is not None:
            room.delete()


@pytest.fixture
def built_world() -> Iterator[orchestrator.BuildSummary]:
    """Run ``build_all()`` once; yield the summary; tear the world down."""
    summary = orchestrator.build_all()
    try:
        yield summary
    finally:
        _teardown_world()


@pytest.mark.django_db
def test_build_all_populates_world(built_world: orchestrator.BuildSummary) -> None:
    """A booted world has the four managers, rooms/exits, the recall point, and mobs."""
    summary = built_world

    for key in MANAGER_KEYS:
        assert search_script(key), f"{key} must exist after build_all"

    assert summary.rooms > 0
    assert summary.exits > 0
    assert summary.mobs > 0
    # Recall reachable: the Inner Bailey carries the server-wide recall tag.
    assert search_object_by_tag("inner_bailey")
    # The summary's mob count matches the live spawned-mob instances on the map.
    live_mobs = [o for o in _spawn_instances() if o.db.spawn_id]
    assert len(live_mobs) == summary.mobs


@pytest.mark.django_db
def test_build_all_is_idempotent(built_world: orchestrator.BuildSummary) -> None:
    """A second build_all() adds no duplicate rooms/exits/NPCs/mobs (§13.4)."""
    first = built_world

    second = orchestrator.build_all()

    assert (second.rooms, second.exits, second.npcs, second.mobs) == (
        first.rooms,
        first.exits,
        first.npcs,
        first.mobs,
    )
    # Exactly one live instance per spawn point — no duplicates piled up.
    spawn_ids = [o.db.spawn_id for o in _spawn_instances() if o.db.spawn_id]
    assert sorted(spawn_ids) == sorted(set(spawn_ids))


@pytest.mark.django_db
def test_leaders_live_and_halt_fires_with_real_scouts(
    built_world: orchestrator.BuildSummary,
) -> None:
    """Every tribe's leaders are live; killing both spawns real rival scouts (§13.5)."""
    tribes = _cave_tribes_with_leaders()
    assert tribes, "at least one cave tribe must have both a chief and a shaman"

    # Each tribe's chief and shaman stand as live instances after the boot pass.
    for faction, roles in tribes.items():
        for role, point in roles.items():
            assert _live(point.spawn_id) is not None, f"{faction} {role} should be live"

    repop = search_script("repop_manager")[0]
    factions = search_script("faction_manager")[0]
    kobold = tribes["kobold"]
    baseline_tension = factions.get_tension("kobold", "orc_vol")

    # Drop both kobold leaders: their deaths report to the repop_manager.
    for role in ("chief", "shaman"):
        _live(kobold[role].spawn_id).at_death()

    # The tribe freezes (repop.md §3).
    halted_until = (repop.db.halted_until or {}).get("kobold")
    assert halted_until is not None and halted_until > time.time()

    # The designated rival (orc_vol) sends a scouting party that stands as REAL
    # mob instances in the kobold lair — the M6 <-> M15 tie (§13.5).
    scouts = repop.db.scouts or {}
    assert scouts, "a rival scouting party should be recorded"
    for scout_id, fields in scouts.items():
        assert fields["faction"] == "orc_vol"
        assert fields["scouting"] == "kobold"
        instance = _live(scout_id)
        assert instance is not None, f"real scout instance {scout_id} should stand in the lair"
        assert instance.db.faction_id == "orc_vol"

    # The halt applied the R2 leadership_broken tension spike with the rival.
    assert factions.get_tension("kobold", "orc_vol") > baseline_tension
