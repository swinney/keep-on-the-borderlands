"""Phase 0 test stubs for the henchmen system (R5).

Derived from openspec/changes/b2-mud-v1-design/specs/henchmen/spec.md and
docs/specs/henchmen.md §7. Docstring-only; Phase 2 unskips and implements.
"""

import pytest

pytestmark = pytest.mark.skip(reason="Phase 0 stub — implementation in Phase 2")


def test_successful_hire_joins_party() -> None:
    """WHEN a reaction roll accepts THEN the fee is charged and the henchman joins."""


def test_refused_hire_costs_nothing() -> None:
    """WHEN a reaction roll refuses THEN no fee is charged and no henchman joins."""


def test_hire_blocked_at_charisma_cap() -> None:
    """WHEN a player at their CHA cap hires THEN the hire is refused."""


def test_following_henchman_moves_with_employer() -> None:
    """WHEN the employer moves and the henchman follows THEN it moves to the same room."""


def test_henchman_attacks_employer_target() -> None:
    """WHEN in combat with no overriding order THEN the henchman attacks the employer's target."""


def test_half_xp_share_reduces_employer_gain() -> None:
    """WHEN a kill grants XP with a henchman present THEN it gets a half share, reducing the employer's."""


def test_shorting_share_lowers_loyalty() -> None:
    """WHEN the player underpays a treasure share THEN loyalty decreases."""


def test_fair_share_raises_loyalty() -> None:
    """WHEN the player pays a fair treasure share THEN loyalty increases."""


def test_failed_morale_routs_henchman() -> None:
    """WHEN a morale trigger fires and 2d6 exceeds loyalty THEN the henchman flees."""


def test_low_loyalty_refuses_suicidal_order() -> None:
    """WHEN a low-loyalty henchman is given a suicidal order THEN it refuses."""


def test_loyalty_adjusts_per_event_table() -> None:
    """WHEN loyalty events occur THEN loyalty changes by the tabled deltas."""


def test_dead_henchman_permanently_removed() -> None:
    """WHEN a henchman reaches 0 HP THEN it is removed permanently and the slot frees."""


def test_roster_refreshes_each_season() -> None:
    """WHEN a season resets THEN the roster refreshes and no prior henchmen persist."""
