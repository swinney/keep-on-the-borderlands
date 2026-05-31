"""Phase 0 test stubs for seasonal reset (R6).

Derived from openspec/changes/b2-mud-v1-design/specs/seasonal-reset/spec.md and
docs/specs/seasonal-reset.md §6. Docstring-only; Phase 2 unskips and implements.
"""

import pytest

pytestmark = pytest.mark.skip(reason="Phase 0 stub — implementation in Phase 2")


def test_reset_invokes_each_manager_hook() -> None:
    """WHEN the reset runs THEN faction, repop, priest, and Shrine each reset."""


def test_reset_reseeds_faction_tension() -> None:
    """WHEN the reset runs THEN tension reseeds to the matrix and standings clear."""


def test_reset_preserves_player_data() -> None:
    """WHEN a season resets THEN level, XP, gear, and bank are unchanged."""


def test_reset_increments_season_number() -> None:
    """WHEN the reset completes THEN the season number increments and start time updates."""


def test_reset_snapshots_leaderboard_before_advancing() -> None:
    """WHEN a season resets THEN survivors are snapshotted before the new season opens."""


def test_reset_rebuilds_instances_and_roster() -> None:
    """WHEN the reset runs THEN mob/room instances rebuild and the henchmen roster refreshes."""


def test_season_global_quest_effects_revert() -> None:
    """WHEN a season resets THEN a destroyed Shrine is rebuilt."""


def test_warning_broadcasts_fire() -> None:
    """WHEN the season nears its boundary THEN T-24h and T-1h warnings fire."""


def test_end_season_runs_immediately() -> None:
    """WHEN end_season fires THEN the full reset runs at once with a bespoke broadcast."""


def test_leaderboard_exposes_both_scopes() -> None:
    """WHEN viewing the leaderboard THEN both per-season and all-time views are available."""


def test_season_length_is_configurable() -> None:
    """WHEN the configured length changes THEN the next boundary uses the new length."""
