"""Tests for XP thresholds and level lookup in world.rules.progression."""

from __future__ import annotations

import pytest

from world.rules.progression import level_for_xp, xp_for_level
from world.rules.saves import CharacterClass

# ---------------------------------------------------------------------------
# xp_for_level
# ---------------------------------------------------------------------------


def test_xp_for_level_one_is_zero() -> None:
    """Level 1 XP is 0 for every class."""
    for char_class in CharacterClass:
        assert xp_for_level(char_class, 1) == 0


def test_xp_for_level_increases_monotonically() -> None:
    """XP thresholds increase at every level for a selection of classes."""
    for char_class in (CharacterClass.FIGHTER, CharacterClass.THIEF, CharacterClass.ELF):
        table_len = 8 if char_class == CharacterClass.HALFLING else 10
        for lvl in range(1, table_len):
            assert xp_for_level(char_class, lvl) < xp_for_level(char_class, lvl + 1)


@pytest.mark.parametrize(
    "char_class, level, expected",
    [
        (CharacterClass.CLERIC, 4, 6000),
        (CharacterClass.FIGHTER, 5, 16000),
        (CharacterClass.MAGIC_USER, 3, 5000),
        (CharacterClass.THIEF, 6, 20000),
        (CharacterClass.DWARF, 7, 70000),
        (CharacterClass.ELF, 2, 4000),
        (CharacterClass.HALFLING, 8, 120000),
    ],
)
def test_xp_for_level_spot_checks(char_class: CharacterClass, level: int, expected: int) -> None:
    """Spot-check specific SRD values for xp_for_level."""
    assert xp_for_level(char_class, level) == expected


def test_xp_for_level_rejects_level_zero() -> None:
    """Level 0 raises ValueError."""
    with pytest.raises(ValueError):
        xp_for_level(CharacterClass.FIGHTER, 0)


def test_xp_for_level_rejects_above_cap() -> None:
    """Level above class cap raises ValueError (Fighter 11, Halfling 9)."""
    with pytest.raises(ValueError):
        xp_for_level(CharacterClass.FIGHTER, 11)
    with pytest.raises(ValueError):
        xp_for_level(CharacterClass.HALFLING, 9)


def test_halfling_caps_at_eight() -> None:
    """Halfling level 8 succeeds; level 9 raises ValueError."""
    assert xp_for_level(CharacterClass.HALFLING, 8) == 120000
    with pytest.raises(ValueError):
        xp_for_level(CharacterClass.HALFLING, 9)


# ---------------------------------------------------------------------------
# level_for_xp
# ---------------------------------------------------------------------------


def test_level_for_xp_zero_is_level_one() -> None:
    """XP of 0 yields level 1 for all classes."""
    for char_class in CharacterClass:
        assert level_for_xp(char_class, 0) == 1


def test_level_for_xp_at_threshold() -> None:
    """At exactly the threshold XP, the character has reached that level."""
    assert level_for_xp(CharacterClass.CLERIC, 1500) == 2
    assert level_for_xp(CharacterClass.FIGHTER, 8000) == 4
    assert level_for_xp(CharacterClass.ELF, 64000) == 6


def test_level_for_xp_just_below_threshold() -> None:
    """One below a threshold stays at the previous level."""
    assert level_for_xp(CharacterClass.CLERIC, 1499) == 1
    assert level_for_xp(CharacterClass.FIGHTER, 7999) == 3
    assert level_for_xp(CharacterClass.MAGIC_USER, 9999) == 3


def test_level_for_xp_rejects_negative() -> None:
    """Negative XP raises ValueError."""
    with pytest.raises(ValueError):
        level_for_xp(CharacterClass.FIGHTER, -1)
