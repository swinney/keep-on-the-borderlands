"""Contract for the pure dice module (M1).

Derived from docs/specs/combat.md §4 (`roll = 1d20 + ...`, `NdM(+K)` notation)
and the testability seam in ADR 0004. These tests are intentionally NOT skipped:
they define the behavior `world.rules.dice` must satisfy.

Randomness is isolated by injecting a seeded `random.Random`, so rolls are
fully reproducible under test without touching global state.
"""

import random

import pytest
from world.rules import dice

# ── parsing ────────────────────────────────────────────────────────────────


def test_parse_simple_notation() -> None:
    """WHEN parsing "1d20" THEN count=1, sides=20, modifier=0."""
    assert dice.parse("1d20") == dice.DiceRoll(count=1, sides=20, modifier=0)


def test_parse_implicit_count() -> None:
    """WHEN the count is omitted ("d6") THEN it defaults to 1."""
    assert dice.parse("d6") == dice.DiceRoll(count=1, sides=6, modifier=0)


def test_parse_positive_modifier() -> None:
    """WHEN parsing "3d6+2" THEN the modifier is +2."""
    assert dice.parse("3d6+2") == dice.DiceRoll(count=3, sides=6, modifier=2)


def test_parse_negative_modifier() -> None:
    """WHEN parsing "1d8-1" THEN the modifier is -1."""
    assert dice.parse("1d8-1") == dice.DiceRoll(count=1, sides=8, modifier=-1)


def test_parse_is_whitespace_and_case_insensitive() -> None:
    """WHEN parsing " 2D6 + 1 " THEN surrounding space and case are tolerated."""
    assert dice.parse(" 2D6 + 1 ") == dice.DiceRoll(count=2, sides=6, modifier=1)


@pytest.mark.parametrize("bad", ["", "d", "2d", "20", "2x6", "1d6+", "0d6", "1d0"])
def test_parse_rejects_malformed(bad: str) -> None:
    """WHEN the notation is malformed or non-positive THEN parse raises ValueError."""
    with pytest.raises(ValueError):
        dice.parse(bad)


# ── rolling ──────────────────────────────────────────────────────────────────


def test_roll_is_reproducible_with_same_seed() -> None:
    """WHEN two rolls use equally-seeded RNGs THEN they produce the same total."""
    assert dice.roll("3d6+1", rng=random.Random(42)) == dice.roll("3d6+1", rng=random.Random(42))


def test_roll_stays_within_bounds() -> None:
    """WHEN rolling "2d6+1" many times THEN every total is in [3, 13]."""
    rng = random.Random(1)
    for _ in range(1000):
        assert 3 <= dice.roll("2d6+1", rng=rng) <= 13


def test_roll_applies_modifier() -> None:
    """WHEN a large modifier is applied THEN it is added to the dice total."""
    assert dice.roll("1d6+100", rng=random.Random(0)) >= 101


def test_roll_dice_returns_each_die() -> None:
    """WHEN rolling the primitive THEN one value per die, each in [1, sides]."""
    rolls = dice.roll_dice(count=4, sides=6, rng=random.Random(7))
    assert len(rolls) == 4
    assert all(1 <= r <= 6 for r in rolls)
