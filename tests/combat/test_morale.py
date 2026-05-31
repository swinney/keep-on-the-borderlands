"""Tests for morale_holds in world.rules.combat."""

from __future__ import annotations

import pytest

from world.rules.combat import morale_holds


def test_morale_holds_when_dice_leq_score() -> None:
    """A roll strictly below the morale score holds morale."""
    assert morale_holds(dice_total=6, morale_score=9) is True


def test_morale_fails_when_dice_gt_score() -> None:
    """A roll above the morale score means the group routs."""
    assert morale_holds(dice_total=10, morale_score=7) is False


def test_morale_exactly_at_score() -> None:
    """A roll equal to the morale score holds morale (boundary)."""
    assert morale_holds(dice_total=8, morale_score=8) is True


def test_morale_rejects_dice_below_two() -> None:
    """A dice_total of 1 (below 2d6 minimum) raises ValueError."""
    with pytest.raises(ValueError):
        morale_holds(dice_total=1, morale_score=9)


def test_morale_rejects_dice_above_twelve() -> None:
    """A dice_total of 13 (above 2d6 maximum) raises ValueError."""
    with pytest.raises(ValueError):
        morale_holds(dice_total=13, morale_score=9)
