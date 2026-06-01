"""Tests for tribe-scoped repop (R3 / docs/specs/repop.md §7).

Un-skipped progressively across M6 tasks:
  Task 1 (this commit): spawn-point registration + standard respawn — behavior 1
  Task 2: leadership halt — behaviors 2, 3, 4, 5
  Task 3: rival scouting — behaviors 6, 7, 8
  Task 4: Shrine reset — behavior 9
  Task 5: season_manager reset — behavior 10

The implemented tests exercise the pure core (world.repop.state) without booting
Evennia, mirroring tests/faction.
"""

from __future__ import annotations

from typing import Any

import pytest

from world.repop import config as cfg
from world.repop.state import RepopState, SpawnPoint


def _point(spawn_id: str = "kobold_guard_1", **overrides: Any) -> SpawnPoint:
    fields: dict[str, Any] = {
        "room": "caves:kobold:guardroom",
        "mob_template": "kobold_warrior",
        "faction": "kobold",
    }
    fields.update(overrides)
    return SpawnPoint(spawn_id=spawn_id, **fields)


# ── M6 Task 1: spawn-point registration + standard respawn ──────────────────


def test_registered_point_starts_alive() -> None:
    """WHEN a spawn point is registered THEN it is populated, with no pending timer."""
    state = RepopState()
    point = _point()
    state.register(point)
    assert state.is_registered(point.spawn_id)
    assert point in state.spawn_points()
    assert not state.is_pending(point.spawn_id)
    assert state.due_spawns(now=10_000.0) == ()


def test_default_respawn_delay_is_standard() -> None:
    """A spawn point with no explicit delay inherits STANDARD_RESPAWN (15 min)."""
    assert _point().respawn_seconds == cfg.STANDARD_RESPAWN == 15 * 60


def test_standard_mob_respawns_after_delay() -> None:
    """WHEN a standard mob dies and STANDARD_RESPAWN elapses THEN it respawns."""
    state = RepopState()
    point = _point()
    state.register(point)

    state.notify_death(point.spawn_id, now=1_000.0)
    assert state.is_pending(point.spawn_id)
    assert state.respawn_at(point.spawn_id) == 1_000.0 + cfg.STANDARD_RESPAWN

    # Not yet due one second before the delay elapses.
    assert state.due_spawns(now=1_000.0 + cfg.STANDARD_RESPAWN - 1) == ()
    # Due exactly once the full delay has passed.
    assert state.due_spawns(now=1_000.0 + cfg.STANDARD_RESPAWN) == (point.spawn_id,)

    # The manager re-instantiates and clears the timer; the point is alive again.
    state.mark_respawned(point.spawn_id)
    assert not state.is_pending(point.spawn_id)
    assert state.due_spawns(now=1_000_000.0) == ()


def test_per_point_respawn_delay_is_honored() -> None:
    """WHEN a point sets its own respawn_seconds THEN that delay is used, not the default."""
    state = RepopState()
    state.register(_point(spawn_id="cave_rat", respawn_seconds=30))
    state.notify_death("cave_rat", now=0.0)
    assert state.due_spawns(now=29.0) == ()
    assert state.due_spawns(now=30.0) == ("cave_rat",)


def test_due_spawns_are_sorted_and_independent() -> None:
    """Multiple dead points come due independently, reported in sorted order."""
    state = RepopState()
    state.register(_point(spawn_id="b_guard"))
    state.register(_point(spawn_id="a_guard"))
    state.register(_point(spawn_id="c_guard", respawn_seconds=30))

    state.notify_death("b_guard", now=0.0)
    state.notify_death("a_guard", now=0.0)
    state.notify_death("c_guard", now=0.0)

    # Only the short-timer point is due early.
    assert state.due_spawns(now=30.0) == ("c_guard",)
    # The two standard points come due together, sorted by id.
    assert state.due_spawns(now=cfg.STANDARD_RESPAWN) == ("a_guard", "b_guard", "c_guard")


# ── M6 Task 2: leadership halt (skipped until implemented) ───────────────────


@pytest.mark.skip(reason="M6 Task 2 — leadership halt")
def test_killing_one_leader_does_not_halt() -> None:
    """WHEN only the chief dies THEN the tribe keeps repopping and the chief returns in 15 min."""


@pytest.mark.skip(reason="M6 Task 2 — leadership halt")
def test_both_leaders_dead_triggers_halt() -> None:
    """WHEN the shaman dies while the chief is dead THEN repop halts 60 min and broadcasts."""


@pytest.mark.skip(reason="M6 Task 2 — leadership halt")
def test_nothing_repops_during_halt() -> None:
    """WHEN a tribe is halted THEN no member, including leaders, respawns."""


@pytest.mark.skip(reason="M6 Task 2 — leadership halt")
def test_halt_expiry_regroups_full_tribe() -> None:
    """WHEN the halt window expires THEN the full tribe respawns with fresh leaders."""


@pytest.mark.skip(reason="M6 Task 2 — leadership halt")
def test_halt_raises_rival_tension() -> None:
    """WHEN a halt triggers THEN leadership_broken raises tension with each rival."""


# ── M6 Task 3: rival scouting (skipped until implemented) ────────────────────


@pytest.mark.skip(reason="M6 Task 3 — rival scouting")
def test_rival_scouts_spawn_in_lair() -> None:
    """WHEN a tribe is halted THEN SCOUT_PARTY_SIZE rival mobs spawn in its lair."""


@pytest.mark.skip(reason="M6 Task 3 — rival scouting")
def test_scouts_count_as_rival_faction() -> None:
    """WHEN a player kills a scout THEN standing changes with the rival, not the broken tribe."""


@pytest.mark.skip(reason="M6 Task 3 — rival scouting")
def test_scouts_retreat_on_regroup() -> None:
    """WHEN the halt expires THEN surviving scouts despawn."""


# ── M6 Task 4 / 5: Shrine reset + season reset (skipped until implemented) ───


@pytest.mark.skip(reason="M6 Task 4 — Shrine reset")
def test_shrine_resets_every_24h_with_broadcast() -> None:
    """WHEN SHRINE_RESET elapses THEN Shrine mobs respawn and a server-wide broadcast fires."""


@pytest.mark.skip(reason="M6 Task 5 — season_manager reset")
def test_season_reset_clears_repop_state() -> None:
    """WHEN a season resets THEN all timers, halts, and scouts clear and the world rebuilds."""
