"""Henchmen hire-flow rules: retainer cap, reaction threshold, loyalty seeding.

docs/specs/henchmen.md §1-§3. Pure (no Evennia); all functions are
value-in / value-out so the hire flow is unit-testable without booting the
server or a database.

Call-site pattern (same as morale_holds): the Evennia manager rolls 2d6, adds
ability_modifier(cha_score), and passes the total to attempt_hire().
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

# ---------------------------------------------------------------------------
# OSE maximum retainers by CHA score (henchmen.md §3)
# ---------------------------------------------------------------------------
RETAINER_CAP_BY_CHA: dict[int, int] = {
    3: 1,
    4: 2,
    5: 2,
    6: 3,
    7: 3,
    8: 3,
    9: 4,
    10: 4,
    11: 4,
    12: 4,
    13: 5,
    14: 5,
    15: 5,
    16: 6,
    17: 6,
    18: 7,
}

HARD_SERVER_CAP: int = 7

# Reaction-roll threshold for hiring (henchmen.md §1): ≤ this → refuses.
REACTION_REFUSE_AT_OR_BELOW: int = 5

# ---------------------------------------------------------------------------
# OSE loyalty modifier by CHA score (henchmen.md §2)
# Separate from the reaction/attack modifier used by ability_modifier().
# ---------------------------------------------------------------------------
# Reaction-band thresholds used in _seed_loyalty (avoid PLR2004 magic-value lint).
_REACTION_GRUDGING_MAX: int = 8  # 6-8 roll: grudging hire
_REACTION_RELIABLE_MAX: int = 11  # 9-11 roll: reliable hire; 12 = loyal

LOYALTY_MOD_BY_CHA: dict[int, int] = {
    3: -2,
    4: -1,
    5: -1,
    6: 0,
    7: 0,
    8: 0,
    9: 0,
    10: 0,
    11: 0,
    12: 0,
    13: 1,
    14: 1,
    15: 1,
    16: 2,
    17: 2,
    18: 4,
}


# ---------------------------------------------------------------------------
# Hire-flow types
# ---------------------------------------------------------------------------


class HireOutcome(Enum):
    """Outcome of a single hire attempt."""

    ACCEPTED = "accepted"
    REFUSED = "refused"  # reaction roll ≤ REACTION_REFUSE_AT_OR_BELOW
    CAP_REACHED = "cap_reached"  # player is already at their CHA retainer limit


@dataclass(frozen=True, slots=True)
class HireResult:
    """Return value of attempt_hire()."""

    outcome: HireOutcome
    fee_paid: int = 0
    initial_loyalty: int = 0


# ---------------------------------------------------------------------------
# Pure hire-flow functions
# ---------------------------------------------------------------------------


def retainer_cap(cha_score: int) -> int:
    """Return the OSE maximum retainers for *cha_score*, capped at HARD_SERVER_CAP.

    Raises ValueError for scores outside the legal 3d6 range.
    """
    try:
        return min(RETAINER_CAP_BY_CHA[cha_score], HARD_SERVER_CAP)
    except KeyError:
        raise ValueError(f"CHA score must be in 3..18, got {cha_score}") from None


def _seed_loyalty(cha_score: int, reaction_total: int) -> int:
    """Seed initial loyalty: CHA loyalty modifier + reaction-roll band, clamped [3, 12].

    Reaction-roll bands -> base loyalty (henchmen.md §2 loyalty table):
        <= 8  -> 7  (grudging / reliable-floor)
        9-11  -> 8  (reliable)
        12    -> 9  (loyal)
    """
    loyalty_mod = LOYALTY_MOD_BY_CHA.get(cha_score, 0)
    if reaction_total <= _REACTION_GRUDGING_MAX:
        base = 7
    elif reaction_total <= _REACTION_RELIABLE_MAX:
        base = 8
    else:
        base = 9
    return max(3, min(12, base + loyalty_mod))


def attempt_hire(
    *,
    cha_score: int,
    hire_fee: int,
    current_party_size: int,
    reaction_roll_total: int,
) -> HireResult:
    """Resolve a hire attempt given a pre-computed reaction roll total.

    Steps (henchmen.md §1, §3):
    1. If *current_party_size* >= retainer_cap(*cha_score*): return CAP_REACHED.
    2. If *reaction_roll_total* <= REACTION_REFUSE_AT_OR_BELOW: return REFUSED.
    3. Otherwise: return ACCEPTED with fee_paid and seeded loyalty.
    """
    cap = retainer_cap(cha_score)
    if current_party_size >= cap:
        return HireResult(outcome=HireOutcome.CAP_REACHED)
    if reaction_roll_total <= REACTION_REFUSE_AT_OR_BELOW:
        return HireResult(outcome=HireOutcome.REFUSED)
    loyalty = _seed_loyalty(cha_score, reaction_total=reaction_roll_total)
    return HireResult(outcome=HireOutcome.ACCEPTED, fee_paid=hire_fee, initial_loyalty=loyalty)


# ---------------------------------------------------------------------------
# Standing orders (henchmen.md §5)
# ---------------------------------------------------------------------------

ORDER_FOLLOW = "follow"
ORDER_ATTACK = "attack"
ORDER_GUARD = "guard"
ORDER_WAIT = "wait"
ORDER_RETREAT = "retreat"
ORDER_DISMISS = "dismiss"

VALID_ORDERS: frozenset[str] = frozenset(
    {ORDER_FOLLOW, ORDER_ATTACK, ORDER_GUARD, ORDER_WAIT, ORDER_RETREAT, ORDER_DISMISS}
)


def henchman_should_follow(order: str) -> bool:
    """Return True when the henchman should move room-to-room with its employer."""
    return order == ORDER_FOLLOW


def henchman_combat_target(
    *,
    order: str,
    employer_target: object | None,
    own_target: object | None = None,
) -> object | None:
    """Return the henchman's combat target this round (henchmen.md §5).

    "follow" (default): mirror the employer's current target.
    "attack": use the henchman's own assigned target.
    Others ("guard", "wait", "retreat"): no auto-attack (caller handles).
    """
    if order == ORDER_FOLLOW:
        return employer_target
    if order == ORDER_ATTACK:
        return own_target
    return None
