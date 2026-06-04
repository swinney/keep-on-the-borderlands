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
from evennia.objects.models import ObjectDB
from evennia.utils import create
from evennia.utils.search import search_object, search_object_by_tag, search_script

from world.build import loadharness, orchestrator, spawner
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


@pytest.mark.django_db
def test_rebuild_world_repopulates_and_preserves_players(
    built_world: orchestrator.BuildSummary,
) -> None:
    """rebuild_world despawns stale instances + re-populates; player data untouched (§13.9)."""
    summary = built_world
    kobold_chief = _cave_tribes_with_leaders()["kobold"]["chief"]

    # A live chief instance stands before the rebuild.
    before = _live(kobold_chief.spawn_id)
    assert before is not None
    before_pk = before.pk

    # A player character with XP/gear/coin/bank that the rebuild must NOT touch.
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="wb-pc-persist")
    gear = create.create_object("typeclasses.objects.Object", key="wb-gear-persist", location=char)
    try:
        char.traits.level.base = 5
        char.traits.xp.current = 12000
        char.db.coin = 33
        char.db.bank_balance = 410
        char_pk = char.pk

        rebuilt = orchestrator.rebuild_world()

        # The world re-populated to the same shape, but the stale chief instance
        # was despawned and re-spawned fresh (a new object, not the survivor).
        assert rebuilt.mobs == summary.mobs
        after = _live(kobold_chief.spawn_id)
        assert after is not None
        assert after.pk != before_pk
        assert not ObjectDB.objects.filter(pk=before_pk).exists()

        # Player-persisted state is untouched (spec §10; R6 persistence boundary).
        assert ObjectDB.objects.filter(pk=char_pk).exists()
        assert int(char.traits.level.value) == 5
        assert int(char.traits.xp.current) == 12000
        assert char.db.coin == 33
        assert char.db.bank_balance == 410
        assert gear.location == char
    finally:
        for item in list(char.contents):
            item.delete()
        if char.pk is not None:
            char.delete()


@pytest.mark.django_db
def test_run_load_reports_driven_population(built_world: orchestrator.BuildSummary) -> None:
    """The load harness drives the requested sessions and reports them (§11)."""
    report = loadharness.run_load(3, build=False)

    # It reports the population it actually drove — never silently capped (§11).
    assert report.requested_sessions == 3
    assert report.driven_sessions == 3
    assert report.commands_run == 3 * len(loadharness.DEFAULT_COMMAND_MIX)
    assert report.latency.samples == report.commands_run
    assert report.recall_built is True
    # The harness tore down its own synthetic sessions — no loadbots linger.
    assert not search_object("loadbot-0")


@pytest.mark.django_db
def test_run_load_reports_unbuilt_world_honestly() -> None:
    """With no recall room (unbuilt world) the harness drives nothing, reports it (§11)."""
    # No built_world fixture: there is no 'inner_bailey' recall point to connect to.
    assert not search_object_by_tag("inner_bailey")

    report = loadharness.run_load(5, build=False)

    # It does not silently cap to a full run: it surfaces the unbuilt world.
    assert report.recall_built is False
    assert report.requested_sessions == 5
    assert report.driven_sessions == 0
    assert report.commands_run == 0
    assert report.latency.samples == 0
    # No location-less loadbots were spawned.
    assert not search_object("loadbot-0")
