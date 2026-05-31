"""Ability scores and the OSE modifier table (pure, Evennia-free).

docs/specs/combat.md §1: six scores generated 3d6-in-order, mapped to modifiers
by the irregular OSE table. The table is written out explicitly rather than
computed so it can be eyeballed against the SRD.
"""

from __future__ import annotations

import random
from dataclasses import asdict, dataclass

from world.rules import dice

# OSE modifier table (docs/specs/combat.md §1). Scores run 3-18 (3d6).
_MODIFIER_BY_SCORE: dict[int, int] = {
    3: -3,
    4: -2,
    5: -2,
    6: -1,
    7: -1,
    8: -1,
    9: 0,
    10: 0,
    11: 0,
    12: 0,
    13: 1,
    14: 1,
    15: 1,
    16: 2,
    17: 2,
    18: 3,
}

# The six scores, in OSE roll order (used for 3d6-in-order generation).
ABILITY_NAMES = ("strength", "intelligence", "wisdom", "dexterity", "constitution", "charisma")


def ability_modifier(score: int) -> int:
    """Return the OSE modifier for an ability ``score`` in [3, 18].

    Raises ``ValueError`` for any score outside the legal 3d6 range.
    """
    try:
        return _MODIFIER_BY_SCORE[score]
    except KeyError:
        raise ValueError(f"ability score must be in 3..18, got {score}") from None


@dataclass(frozen=True, slots=True)
class AbilityScores:
    """A character's six ability scores."""

    strength: int
    intelligence: int
    wisdom: int
    dexterity: int
    constitution: int
    charisma: int

    def as_dict(self) -> dict[str, int]:
        """Return the scores keyed by ability name."""
        return asdict(self)


def roll_ability_scores(*, rng: random.Random) -> AbilityScores:
    """Roll ``3d6`` for each ability in order (OSE).

    The creation-time single-swap allowance is applied by the character-creation
    flow (a later milestone), not here — this returns the raw rolled scores.
    """
    rolled = {name: dice.roll("3d6", rng=rng) for name in ABILITY_NAMES}
    return AbilityScores(**rolled)
