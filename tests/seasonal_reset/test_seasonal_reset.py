"""Tests for seasonal reset (R6 / docs/specs/seasonal-reset.md §6).

Un-skipped progressively across the M6 season tasks:
  Task 5 (this commit): season_manager orchestration — behaviors 1, 2, 4, 5, 6,
    7, 8, 9, 10, and configurable season length (§1).
  Task 6: engine-level player-data persistence — behavior 3.

The implemented tests exercise the pure core (world.season.*) without booting
Evennia, mirroring tests/faction and tests/repop. The season_manager GlobalScript
is a thin Evennia wrapper over this core (clock, real hooks, persistence).
"""

from __future__ import annotations

import pytest

from world.factions.state import FactionState
from world.season import config as cfg
from world.season.leaderboard import FELL, SURVIVED, Leaderboard, Survivor
from world.season.state import ResetReport, SeasonState, run_reset


class RecordingHooks:
    """A ResetHooks double that records the order in which hooks fire."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def reset_factions(self) -> None:
        self.calls.append("factions")

    def reset_repop(self) -> None:
        self.calls.append("repop")

    def reset_priest(self) -> None:
        self.calls.append("priest")

    def reset_shrine(self) -> None:
        self.calls.append("shrine")

    def revert_season_quests(self) -> None:
        self.calls.append("quests")

    def rebuild_world(self) -> None:
        self.calls.append("rebuild")

    def refresh_roster(self) -> None:
        self.calls.append("roster")


def _survivors() -> list[Survivor]:
    return [
        Survivor(character_name="Aldra", char_class="cleric", level=5, hardcore=False),
        Survivor(character_name="Borin", char_class="fighter", level=8, hardcore=True),
    ]


# ── Behavior 1: reset invokes each world-manager hook ────────────────────────


def test_reset_invokes_each_manager_hook() -> None:
    """WHEN the reset runs THEN faction, repop, priest, and Shrine each reset."""
    state = SeasonState(season_number=3, season_start=0.0)
    hooks = RecordingHooks()

    run_reset(state, Leaderboard(), hooks, [], now=state.season_end())

    for manager in ("factions", "repop", "priest", "shrine"):
        assert manager in hooks.calls
    # The four world managers flush before the world is rebuilt (spec §3 order).
    assert hooks.calls.index("shrine") < hooks.calls.index("rebuild")


# ── Behavior 2: reset reseeds faction tension and clears standings ───────────


def test_reset_reseeds_faction_tension() -> None:
    """WHEN the reset runs THEN tension reseeds to the matrix and standings clear."""
    factions = FactionState()
    factions.apply_quest_aid_vs("kobold", "orc_vol")  # dirties a pair tension
    factions.apply_kill_member("kobold", "player#1")  # dirties a player standing
    assert factions.standings
    pristine = FactionState().get_tension("kobold", "orc_vol")
    assert factions.get_tension("kobold", "orc_vol") != pristine

    class FactionHooks(RecordingHooks):
        def reset_factions(self) -> None:
            super().reset_factions()
            factions.reset_season()

    run_reset(SeasonState(), Leaderboard(), FactionHooks(), [], now=0.0)

    assert factions.standings == {}
    assert factions.get_tension("kobold", "orc_vol") == pristine


# ── Behavior 4: reset increments the season number and start time ────────────


def test_reset_increments_season_number() -> None:
    """WHEN the reset completes THEN the season number increments and start updates."""
    state = SeasonState(season_number=4, season_start=1_000.0)
    state.mark_warned(cfg.WARN_OFFSETS[0])

    report = run_reset(state, Leaderboard(), RecordingHooks(), [], now=5_000.0)

    assert isinstance(report, ResetReport)
    assert state.season_number == 5
    assert state.season_start == 5_000.0
    assert report.closing_season == 4
    assert report.new_season == 5
    assert report.new_start == 5_000.0
    # A fresh season starts with no warnings fired.
    assert state.warned == set()


# ── Behavior 5: reset snapshots the leaderboard before advancing ─────────────


def test_reset_snapshots_leaderboard_before_advancing() -> None:
    """WHEN a season resets THEN survivors are snapshotted before the new season opens."""
    state = SeasonState(season_number=7, season_start=0.0)
    board = Leaderboard()

    report = run_reset(state, board, RecordingHooks(), _survivors(), now=42.0)

    # Survivors are recorded under the *closing* season (7), proving the snapshot
    # ran before the counter advanced to 8 (spec §3.2).
    snapped = board.per_season(7)
    assert len(snapped) == len(_survivors()) == report.survivors_recorded
    assert {e.outcome for e in snapped} == {SURVIVED}
    assert all(e.recorded_at == 42.0 for e in snapped)
    assert board.per_season(8) == ()  # nothing recorded under the new season


# ── Behavior 6: reset rebuilds instances and refreshes the roster ────────────


def test_reset_rebuilds_instances_and_roster() -> None:
    """WHEN the reset runs THEN mob/room instances rebuild and the roster refreshes."""
    hooks = RecordingHooks()

    run_reset(SeasonState(), Leaderboard(), hooks, [], now=0.0)

    assert "rebuild" in hooks.calls
    assert "roster" in hooks.calls
    # Season-global quest effects revert before the world rebuilds (spec §3.4-5).
    assert hooks.calls.index("quests") < hooks.calls.index("rebuild")


# ── Behavior 7: season-global quest effects revert ───────────────────────────


def test_season_global_quest_effects_revert() -> None:
    """WHEN a season resets THEN a destroyed Shrine is rebuilt (quest effects revert)."""
    hooks = RecordingHooks()

    run_reset(SeasonState(), Leaderboard(), hooks, [], now=0.0)

    assert "quests" in hooks.calls


# ── Behavior 8: pre-boundary warnings and the new-season broadcast ───────────


def test_warning_broadcasts_fire() -> None:
    """WHEN the season nears its boundary THEN T-24h and T-1h warnings fire once each."""
    state = SeasonState(season_number=1, season_start=0.0, length_seconds=cfg.SEASON_LENGTH)
    end = state.season_end()
    day, hour = cfg.WARN_OFFSETS

    # Nothing due early in the season.
    assert state.due_warnings(now=0.0) == ()
    # At T-24h the day-out warning is due (longest offset first).
    assert state.due_warnings(now=end - day) == (day,)

    state.mark_warned(day)
    # It does not re-fire once marked; the T-1h warning is still pending.
    assert state.due_warnings(now=end - day) == ()
    assert state.due_warnings(now=end - hour) == (hour,)

    # The new-season broadcast copy exists for the manager to send after a reset.
    assert cfg.NEW_SEASON_BROADCAST


# ── Behavior 9: end_season runs the full reset immediately ───────────────────


def test_end_season_runs_immediately() -> None:
    """WHEN end_season fires THEN the full reset runs at once, ahead of the timer."""
    state = SeasonState(season_number=2, season_start=0.0)
    board = Leaderboard()

    # The season is nowhere near its timed end...
    assert not state.is_expired(now=10.0)
    # ...yet an early end (e.g. the Shrine destroyed) runs the full reset now.
    report = run_reset(
        state, board, RecordingHooks(), _survivors(), now=10.0, reason="shrine_destroyed"
    )

    assert report.reason == "shrine_destroyed"
    assert state.season_number == 3
    assert state.season_start == 10.0
    assert len(board.per_season(2)) == len(_survivors())
    # The manager delivers this bespoke framing for an early end (spec §5).
    assert cfg.EARLY_END_BROADCAST


# ── Behavior 10: leaderboard exposes per-season and all-time views ───────────


def test_leaderboard_exposes_both_scopes() -> None:
    """WHEN viewing the leaderboard THEN both per-season and all-time views exist."""
    board = Leaderboard()
    # A hardcore death is recorded immediately, mid-season (spec §4; R7).
    board.append_fell("Doomed", "magic-user", level=3, season_number=1, recorded_at=5.0)
    # Survivors are recorded only at the reset snapshot.
    board.snapshot_survivors(1, _survivors(), recorded_at=100.0)

    season_one = board.per_season(1)
    assert len(season_one) == 1 + len(_survivors())
    outcomes = {e.character_name: e.outcome for e in season_one}
    assert outcomes["Doomed"] == FELL
    assert outcomes["Borin"] == SURVIVED

    # The all-time view spans seasons and ranks by level (highest first).
    legend = board.append_fell("Legend", "fighter", level=10, season_number=2, recorded_at=200.0)
    all_time = board.all_time()
    assert all_time[0].character_name == "Legend"
    assert all_time[0].level == 10
    assert {e.season_number for e in all_time} == {1, 2}
    # The per-season view isolates the new season's lone entry.
    assert board.per_season(2) == (legend,)


# ── §1: season length is configurable ────────────────────────────────────────


def test_season_length_is_configurable() -> None:
    """WHEN the configured length changes THEN the next boundary uses the new length."""
    default = SeasonState(season_start=0.0)
    assert default.season_end() == cfg.SEASON_LENGTH

    short = SeasonState(season_start=0.0, length_seconds=7 * 24 * 60 * 60)
    assert short.season_end() == 7 * 24 * 60 * 60
    assert not short.is_expired(now=short.season_end() - 1)
    assert short.is_expired(now=short.season_end())


# ── Behavior 3: engine-level persistence (M6 Task 6) ─────────────────────────


@pytest.mark.skip(reason="M6 Task 6 — engine-level player-data persistence check")
def test_reset_preserves_player_data() -> None:
    """WHEN a season resets THEN level, XP, gear, and bank are unchanged."""
