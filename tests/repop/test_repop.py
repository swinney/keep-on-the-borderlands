"""Tests for tribe-scoped repop (R3 / docs/specs/repop.md §7).

Un-skipped progressively across M6 tasks:
  Task 1 (this commit): spawn-point registration + standard respawn — behavior 1
  Task 2: leadership halt — behaviors 2, 3, 4, 5
  Task 3 (this commit): rival scouting — behaviors 6, 7, 8
  Task 4: Shrine reset — behavior 9
  Task 5: season_manager reset — behavior 10

The implemented tests exercise the pure core (world.repop.state) without booting
Evennia, mirroring tests/faction.
"""

from __future__ import annotations

from typing import Any

from world.factions import config as fac_cfg
from world.factions.state import FactionState
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


def _leader(spawn_id: str, role: str, **overrides: Any) -> SpawnPoint:
    """A chief/shaman leader spawn point (defaults to the kobold tribe)."""
    return _point(spawn_id, is_leader=True, leader_role=role, **overrides)


def _halted_kobold_tribe(now: float = 0.0) -> RepopState:
    """A kobold tribe with a guard plus chief and shaman, both leaders dead → halted."""
    state = RepopState()
    state.register(_point("kobold_guard_1"))
    state.register(_leader("kobold_chief", "chief"))
    state.register(_leader("kobold_shaman", "shaman"))
    state.notify_death("kobold_chief", now=now)
    event = state.notify_death("kobold_shaman", now=now + 1.0)
    assert event is not None
    return state


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


# ── M6 Task 2: leadership halt ───────────────────────────────────────────────


def test_killing_one_leader_does_not_halt() -> None:
    """WHEN only the chief dies THEN the tribe keeps repopping and the chief returns in 15 min."""
    state = RepopState()
    state.register(_point("kobold_guard_1"))
    state.register(_leader("kobold_chief", "chief"))
    state.register(_leader("kobold_shaman", "shaman"))

    # Chief alone dies; shaman is still alive → no halt event, tribe not halted.
    event = state.notify_death("kobold_chief", now=0.0)
    assert event is None
    assert not state.is_halted("kobold", now=0.0)

    # The chief returns on the standard 15-min timer, like any other mob.
    assert state.due_spawns(now=cfg.STANDARD_RESPAWN - 1) == ()
    assert state.due_spawns(now=cfg.STANDARD_RESPAWN) == ("kobold_chief",)


def test_killing_a_respawned_then_second_leader_does_not_halt() -> None:
    """WHEN the first leader has already respawned THEN dropping the other does not halt."""
    state = RepopState()
    state.register(_leader("kobold_chief", "chief"))
    state.register(_leader("kobold_shaman", "shaman"))

    state.notify_death("kobold_chief", now=0.0)
    state.mark_respawned("kobold_chief")  # chief back up before the shaman falls
    event = state.notify_death("kobold_shaman", now=10.0)
    assert event is None
    assert not state.is_halted("kobold", now=10.0)


def test_both_leaders_dead_triggers_halt() -> None:
    """WHEN the shaman dies while the chief is dead THEN repop halts 60 min."""
    state = RepopState()
    state.register(_leader("kobold_chief", "chief"))
    state.register(_leader("kobold_shaman", "shaman"))

    assert state.notify_death("kobold_chief", now=1_000.0) is None
    event = state.notify_death("kobold_shaman", now=1_100.0)

    assert event is not None
    assert event.faction == "kobold"
    # The window is measured from the instant both are down (the second death).
    assert event.halted_until == 1_100.0 + cfg.LEADERSHIP_HALT
    assert state.halted_until("kobold") == 1_100.0 + cfg.LEADERSHIP_HALT
    assert state.is_halted("kobold", now=1_100.0)
    assert cfg.LEADERSHIP_HALT == 60 * 60


def test_nothing_repops_during_halt() -> None:
    """WHEN a tribe is halted THEN no member, including leaders, respawns."""
    state = _halted_kobold_tribe(now=0.0)

    # Mid-window: well past the standard timer, yet nothing is due.
    assert state.is_halted("kobold", now=cfg.STANDARD_RESPAWN)
    assert state.due_spawns(now=cfg.STANDARD_RESPAWN) == ()
    # Even one second before expiry the tribe stays frozen.
    assert state.due_spawns(now=1.0 + cfg.LEADERSHIP_HALT - 1) == ()


def test_halt_does_not_freeze_other_tribes() -> None:
    """WHEN one tribe is halted THEN an unrelated tribe still repops normally."""
    state = _halted_kobold_tribe(now=0.0)
    state.register(_point("goblin_guard_1", faction="goblin"))
    state.notify_death("goblin_guard_1", now=0.0)

    assert not state.is_halted("goblin", now=cfg.STANDARD_RESPAWN)
    assert state.due_spawns(now=cfg.STANDARD_RESPAWN) == ("goblin_guard_1",)


def test_halt_expiry_regroups_full_tribe() -> None:
    """WHEN the halt window expires THEN the full tribe respawns with fresh leaders."""
    state = _halted_kobold_tribe(now=0.0)
    expiry = 1.0 + cfg.LEADERSHIP_HALT

    assert not state.is_halted("kobold", now=expiry)
    # The entire tribe — guard, chief, and shaman — comes due together at expiry.
    assert state.due_spawns(now=expiry) == (
        "kobold_chief",
        "kobold_guard_1",
        "kobold_shaman",
    )


def test_halt_raises_rival_tension() -> None:
    """WHEN a halt triggers THEN leadership_broken raises tension with each rival."""
    state = RepopState()
    state.register(_leader("kobold_chief", "chief"))
    state.register(_leader("kobold_shaman", "shaman"))
    state.notify_death("kobold_chief", now=0.0)
    event = state.notify_death("kobold_shaman", now=10.0)
    assert event is not None

    # The manager feeds the broken faction into R2; tension rises with each rival.
    factions = FactionState()
    before = factions.get_tension("kobold", "orc_vol")
    factions.apply_leadership_broken(event.faction)
    after = factions.get_tension("kobold", "orc_vol")
    assert after == before + fac_cfg.RELATION_EVENTS["leadership_broken"]


# ── M6 Task 3: rival scouting ────────────────────────────────────────────────


def test_rival_scouts_spawn_in_lair() -> None:
    """WHEN a tribe is halted THEN SCOUT_PARTY_SIZE rival mobs spawn in its lair."""
    state = _halted_kobold_tribe(now=0.0)

    scouts = state.scouts_for("kobold")
    assert len(scouts) == cfg.SCOUT_PARTY_SIZE == 3
    # All scouts belong to the kobolds' designated rival (orc_vol, spec §4).
    assert cfg.DESIGNATED_RIVAL["kobold"] == "orc_vol"
    assert {s.faction for s in scouts} == {"orc_vol"}
    # They occupy the broken tribe's lair rooms, not anywhere else.
    lair_rooms = {p.room for p in state.spawn_points() if p.faction == "kobold"}
    assert {s.room for s in scouts} <= lair_rooms


def test_solitary_tribe_gets_no_scouts() -> None:
    """WHEN a rival-less (solitary) tribe is halted THEN no scouts move in."""
    state = RepopState()
    state.register(_leader("ogre_chief", "chief", faction="ogre"))
    state.register(_leader("ogre_shaman", "shaman", faction="ogre"))
    state.notify_death("ogre_chief", now=0.0)
    event = state.notify_death("ogre_shaman", now=1.0)

    assert event is not None
    assert cfg.DESIGNATED_RIVAL["ogre"] is None
    assert event.rival is None
    assert state.scouts_for("ogre") == ()


def test_scouts_count_as_rival_faction() -> None:
    """WHEN a player kills a scout THEN standing changes with the rival, not the broken tribe."""
    state = _halted_kobold_tribe(now=0.0)
    scout = state.scouts_for("kobold")[0]

    # The scout is the rival faction for all R2 purposes, never the broken tribe.
    assert scout.faction == cfg.DESIGNATED_RIVAL["kobold"] == "orc_vol"
    assert scout.faction != "kobold"

    # Killing the scout shifts the player's standing with the rival faction only.
    factions = FactionState()
    player = "player#1"
    rival_before = factions.get_standing(scout.faction, player)
    factions.apply_kill_member(scout.faction, player)
    assert factions.get_standing(scout.faction, player) == (
        rival_before + fac_cfg.STANDING_EVENTS["kill_member"]
    )
    assert factions.get_standing("kobold", player) == 0  # broken tribe untouched

    # And the scout leaves the field once slain (it does not respawn).
    state.notify_scout_death(scout.scout_id)
    assert scout.scout_id not in {s.scout_id for s in state.active_scouts()}


def test_scouts_retreat_on_regroup() -> None:
    """WHEN the halt expires THEN surviving scouts despawn."""
    state = _halted_kobold_tribe(now=0.0)
    expiry = 1.0 + cfg.LEADERSHIP_HALT

    # Mid-window the scouts hold the lair; none are due to retreat yet.
    assert state.due_scout_retreats(now=cfg.STANDARD_RESPAWN) == ()
    assert len(state.active_scouts()) == cfg.SCOUT_PARTY_SIZE

    # At halt expiry every surviving scout comes due to retreat, sorted.
    due = state.due_scout_retreats(now=expiry)
    assert due == tuple(s.scout_id for s in state.scouts_for("kobold"))
    for scout_id in due:
        state.mark_scout_retreated(scout_id)
    assert state.active_scouts() == ()


# ── M6 Task 4: Shrine reset ──────────────────────────────────────────────────


def test_shrine_resets_every_24h_with_broadcast() -> None:
    """WHEN SHRINE_RESET elapses THEN the Shrine comes due to reset, on a 24h cadence.

    The pure core exposes the reset *timing*; the repop_manager turns each due
    reset into the wholesale restock plus server-wide broadcast (spec §5), just
    as the leadership-halt broadcast is delegated out of the pure core.
    """
    state = RepopState()
    # Unarmed until scheduled at world build / season start.
    assert state.shrine_reset_at() is None
    assert state.shrine_reset_due(now=0.0) is False

    state.schedule_shrine_reset(now=0.0)
    assert state.shrine_reset_at() == cfg.SHRINE_RESET == 24 * 60 * 60

    # Not due until the full 24h cycle elapses; due exactly once it has passed.
    assert state.shrine_reset_due(now=cfg.SHRINE_RESET - 1) is False
    assert state.shrine_reset_due(now=cfg.SHRINE_RESET) is True

    # Performing the reset re-arms the next cycle and does not re-fire within
    # the same window (idempotent, spec §5).
    state.mark_shrine_reset(now=cfg.SHRINE_RESET)
    assert state.shrine_reset_due(now=cfg.SHRINE_RESET) is False
    assert state.shrine_reset_at() == 2 * cfg.SHRINE_RESET

    # And it resets again on the next 24h boundary — a repeating cadence.
    assert state.shrine_reset_due(now=2 * cfg.SHRINE_RESET - 1) is False
    assert state.shrine_reset_due(now=2 * cfg.SHRINE_RESET) is True


# ── M6 Task 5: season_manager reset ──────────────────────────────────────────


def test_season_reset_clears_repop_state() -> None:
    """WHEN a season resets THEN all timers, halts, and scouts clear and the world rebuilds."""
    state = _halted_kobold_tribe(now=0.0)
    state.register(_point("goblin_guard_1", faction="goblin"))
    state.notify_death("goblin_guard_1", now=0.0)
    state.schedule_shrine_reset(now=0.0)

    # Precondition: the tribe is halted with scouts in its lair and timers pending.
    assert state.is_halted("kobold", now=0.0)
    assert state.active_scouts()
    assert state.is_pending("goblin_guard_1")

    state.reset_season(now=5_000.0)

    # All live wall-clock state is wiped: no halts, no scouts, no pending timers.
    assert not state.is_halted("kobold", now=5_000.0)
    assert state.active_scouts() == ()
    assert state.due_spawns(now=10_000_000.0) == ()
    for point in state.spawn_points():
        assert not state.is_pending(point.spawn_id)

    # The static registry is retained — the world rebuilds from the same points.
    assert state.is_registered("kobold_chief")
    assert state.is_registered("goblin_guard_1")

    # And the Shrine's 24h cycle is re-armed from the reset instant.
    assert state.shrine_reset_at() == 5_000.0 + cfg.SHRINE_RESET
