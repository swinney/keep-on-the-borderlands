"""Tests for the henchmen system (R5 / docs/specs/henchmen.md §7).

Un-skipped progressively across M5 tasks:
  Task 1 (this commit): hire flow — tests 1, 2, 3
  Task 2: follow + orders + combat AI — tests 4, 5
  Task 3: loyalty/morale — tests 6, 7, 8, 9
  Task 4: XP + treasure share + permadeath — tests 10, 11, 12
"""

from __future__ import annotations

import pytest
from evennia.utils import create

from world.rules.henchmen import HireOutcome, attempt_hire, henchman_combat_target, retainer_cap

# ── M5 Task 1: hire flow ───────────────────────────────────────────────────


def test_successful_hire_joins_party() -> None:
    """WHEN a reaction roll accepts THEN the fee is charged and the henchman joins."""
    result = attempt_hire(
        cha_score=12,
        hire_fee=40,
        current_party_size=0,
        reaction_roll_total=9,  # 9 > REACTION_REFUSE_AT_OR_BELOW (5) → accepts
    )
    assert result.outcome == HireOutcome.ACCEPTED
    assert result.fee_paid == 40
    assert result.initial_loyalty > 0


def test_refused_hire_costs_nothing() -> None:
    """WHEN a reaction roll refuses THEN no fee is charged and no henchman joins."""
    result = attempt_hire(
        cha_score=12,
        hire_fee=40,
        current_party_size=0,
        reaction_roll_total=3,  # 3 ≤ REACTION_REFUSE_AT_OR_BELOW (5) → refuses
    )
    assert result.outcome == HireOutcome.REFUSED
    assert result.fee_paid == 0


def test_hire_blocked_at_charisma_cap() -> None:
    """WHEN a player at their CHA cap hires THEN the hire is refused."""
    cap = retainer_cap(12)  # CHA 12 → cap = 4
    result = attempt_hire(
        cha_score=12,
        hire_fee=40,
        current_party_size=cap,  # party is full
        reaction_roll_total=12,  # strong roll, still blocked by cap
    )
    assert result.outcome == HireOutcome.CAP_REACHED
    assert result.fee_paid == 0


# ── M5 Task 2: follow + combat AI ─────────────────────────────────────────


@pytest.mark.django_db
def test_following_henchman_moves_with_employer() -> None:
    """WHEN the employer moves and the henchman follows THEN it moves to the same room."""
    room_a = create.create_object("typeclasses.rooms.Room", key="hm-room-a")
    room_b = create.create_object("typeclasses.rooms.Room", key="hm-room-b")
    employer = create.create_object(
        "typeclasses.characters.PlayerCharacter", key="hm-employer", location=room_a
    )
    henchman = create.create_object("typeclasses.npcs.Henchman", key="hm-follower", location=room_a)
    try:
        henchman.db.employer = employer
        henchman.db.order = "follow"
        employer.move_to(room_b, quiet=True)
        assert henchman.location == room_b
    finally:
        henchman.delete()
        employer.delete()
        room_a.delete()
        room_b.delete()


def test_henchman_attacks_employer_target() -> None:
    """WHEN in combat with no overriding order THEN the henchman attacks the employer's target."""
    mock_target = object()
    result = henchman_combat_target(order="follow", employer_target=mock_target)
    assert result is mock_target


@pytest.mark.skip(reason="Implemented in M5 Task 3")
def test_half_xp_share_reduces_employer_gain() -> None:
    """WHEN a kill grants XP with a henchman present THEN it gets a half share, reducing the employer's."""


@pytest.mark.skip(reason="Implemented in M5 Task 3")
def test_shorting_share_lowers_loyalty() -> None:
    """WHEN the player underpays a treasure share THEN loyalty decreases."""


@pytest.mark.skip(reason="Implemented in M5 Task 3")
def test_fair_share_raises_loyalty() -> None:
    """WHEN the player pays a fair treasure share THEN loyalty increases."""


@pytest.mark.skip(reason="Implemented in M5 Task 3")
def test_failed_morale_routs_henchman() -> None:
    """WHEN a morale trigger fires and 2d6 exceeds loyalty THEN the henchman flees."""


@pytest.mark.skip(reason="Implemented in M5 Task 3")
def test_low_loyalty_refuses_suicidal_order() -> None:
    """WHEN a low-loyalty henchman is given a suicidal order THEN it refuses."""


@pytest.mark.skip(reason="Implemented in M5 Task 3")
def test_loyalty_adjusts_per_event_table() -> None:
    """WHEN loyalty events occur THEN loyalty changes by the tabled deltas."""


@pytest.mark.skip(reason="Implemented in M5 Task 4")
def test_dead_henchman_permanently_removed() -> None:
    """WHEN a henchman reaches 0 HP THEN it is removed permanently and the slot frees."""


@pytest.mark.skip(reason="Implemented in M5 Task 4")
def test_roster_refreshes_each_season() -> None:
    """WHEN a season resets THEN the roster refreshes and no prior henchmen persist."""
