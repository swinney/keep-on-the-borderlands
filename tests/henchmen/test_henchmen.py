"""Tests for the henchmen system (R5 / docs/specs/henchmen.md §7).

Un-skipped progressively across M5 tasks:
  Task 1 (this commit): hire flow — tests 1, 2, 3
  Task 2: follow + orders + combat AI — tests 4, 5
  Task 3: loyalty/morale — tests 6, 7, 8, 9
  Task 4: XP + treasure share + permadeath — tests 10, 11, 12
"""

from __future__ import annotations

import contextlib

import pytest
from evennia.objects.models import ObjectDB
from evennia.utils import create

from world.henchmen import reset_henchmen
from world.rules.combat import morale_holds
from world.rules.henchmen import (
    HireOutcome,
    LoyaltyEvent,
    adjust_loyalty,
    attempt_hire,
    henchman_combat_target,
    loyalty_band_refuses_suicidal,
    retainer_cap,
    split_xp,
)

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


def test_half_xp_share_reduces_employer_gain() -> None:
    """WHEN a kill grants XP with a henchman present THEN it gets a half share, reducing the employer's."""
    xp_full, xp_half = split_xp(total_xp=100, full_shares=1, half_shares=1)
    # henchman earns less than the employer
    assert xp_half < xp_full
    # combined payout does not exceed the pool (rounding may leave a remainder)
    assert xp_full + xp_half <= 100
    # henchman gets exactly half of what the employer earns (integer floor)
    assert xp_half == xp_full // 2


def test_shorting_share_lowers_loyalty() -> None:
    """WHEN the player underpays a treasure share THEN loyalty decreases."""
    assert adjust_loyalty(8, LoyaltyEvent.SHORTED_SHARE) == 6  # 8 - 2


def test_fair_share_raises_loyalty() -> None:
    """WHEN the player pays a fair treasure share THEN loyalty increases."""
    assert adjust_loyalty(7, LoyaltyEvent.FAIR_SHARE) == 8  # 7 + 1


def test_failed_morale_routs_henchman() -> None:
    """WHEN a morale trigger fires and 2d6 exceeds loyalty THEN the henchman flees."""
    # roll exceeds loyalty → morale fails → rout
    assert not morale_holds(dice_total=10, morale_score=7)
    # roll meets loyalty → morale holds → stays
    assert morale_holds(dice_total=7, morale_score=7)


def test_low_loyalty_refuses_suicidal_order() -> None:
    """WHEN a low-loyalty henchman is given a suicidal order THEN it refuses."""
    # grudging band (4-5) refuses
    assert loyalty_band_refuses_suicidal(5)
    assert loyalty_band_refuses_suicidal(4)
    # reliable band (6+) does not refuse
    assert not loyalty_band_refuses_suicidal(6)
    assert not loyalty_band_refuses_suicidal(9)


def test_loyalty_adjusts_per_event_table() -> None:
    """WHEN loyalty events occur THEN loyalty changes by the tabled deltas."""
    base = 8
    assert adjust_loyalty(base, LoyaltyEvent.HEALED) == 9  # +1
    assert adjust_loyalty(base, LoyaltyEvent.ALLY_DIED) == 7  # -1
    assert adjust_loyalty(base, LoyaltyEvent.EMPLOYER_FLED) == 6  # -2
    assert adjust_loyalty(base, LoyaltyEvent.VICTORIOUS_FIGHT) == 9  # +1
    # upper clamp: loyalty 12 + 1 stays 12
    assert adjust_loyalty(12, LoyaltyEvent.VICTORIOUS_FIGHT) == 12
    # lower clamp: loyalty 1 - 2 stays 1
    assert adjust_loyalty(1, LoyaltyEvent.SHORTED_SHARE) == 1


@pytest.mark.django_db
def test_dead_henchman_permanently_removed() -> None:
    """WHEN a henchman reaches 0 HP THEN it is removed permanently and the slot frees."""
    room = create.create_object("typeclasses.rooms.Room", key="hm-perm-room")
    employer = create.create_object(
        "typeclasses.characters.PlayerCharacter", key="hm-perm-employer", location=room
    )
    henchman = create.create_object(
        "typeclasses.npcs.Henchman", key="hm-perm-follower", location=room
    )
    henchman.db.employer = employer
    henchman_id = henchman.id
    try:
        henchman.apply_damage(9999)  # lethal → at_death() → self.delete()
        assert not ObjectDB.objects.filter(id=henchman_id).exists()
    finally:
        with contextlib.suppress(Exception):
            employer.delete()
        with contextlib.suppress(Exception):
            room.delete()


@pytest.mark.django_db
def test_roster_refreshes_each_season() -> None:
    """WHEN a season resets THEN the roster refreshes and no prior henchmen persist."""
    room = create.create_object("typeclasses.rooms.Room", key="hm-season-room")
    henchman = create.create_object(
        "typeclasses.npcs.Henchman", key="hm-season-follower", location=room
    )
    henchman_id = henchman.id
    try:
        reset_henchmen()
        assert not ObjectDB.objects.filter(id=henchman_id).exists()
    finally:
        with contextlib.suppress(Exception):
            room.delete()
