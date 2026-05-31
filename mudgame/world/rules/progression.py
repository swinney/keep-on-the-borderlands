"""Character advancement: hit points, XP thresholds, and level lookup (pure).

docs/specs/combat.md §3: HP gained per level is the class hit die plus the CON
modifier, with a floor of 1 so a bad roll or a negative CON never costs a level.
XP thresholds follow the OSE SRD, written out explicitly so each value can be
eyeballed against the book. Levels run 1..10 (the B2-scaled range, CLAUDE.md §2);
Halfling caps at 8 per the SRD.
"""

from __future__ import annotations

import random

from world.rules.saves import CharacterClass

_MIN_LEVEL = 1

# OSE SRD XP thresholds. Index i is the XP required to reach level (i+1),
# so index 0 is always 0 (level 1 requires no XP). Halfling caps at level 8.
_XP_TABLE: dict[CharacterClass, tuple[int, ...]] = {
    CharacterClass.CLERIC: (0, 1500, 3000, 6000, 12000, 25000, 50000, 100000, 200000, 300000),
    CharacterClass.FIGHTER: (0, 2000, 4000, 8000, 16000, 32000, 64000, 120000, 240000, 360000),
    CharacterClass.MAGIC_USER: (0, 2500, 5000, 10000, 20000, 40000, 80000, 150000, 300000, 450000),
    CharacterClass.THIEF: (0, 1200, 2400, 4800, 9600, 20000, 40000, 80000, 160000, 280000),
    CharacterClass.DWARF: (0, 2200, 4400, 8800, 17000, 35000, 70000, 140000, 270000, 400000),
    CharacterClass.ELF: (0, 4000, 8000, 16000, 32000, 64000, 120000, 250000, 400000, 600000),
    CharacterClass.HALFLING: (0, 2000, 4000, 8000, 16000, 32000, 64000, 120000),
}


def roll_hit_points(*, hit_die: int, con_modifier: int, rng: random.Random) -> int:
    """Roll one level's hit points: ``max(1, 1dHIT_DIE + con_modifier)``."""
    return max(1, rng.randint(1, hit_die) + con_modifier)


def xp_for_level(char_class: CharacterClass, level: int) -> int:
    """Return the XP required to reach ``level`` for ``char_class``.

    Raises ``ValueError`` if ``level`` is below 1 or above the class's defined
    SRD cap (e.g. Halfling above level 8).
    """
    table = _XP_TABLE[char_class]
    cap = len(table)
    if level < _MIN_LEVEL or level > cap:
        raise ValueError(f"{char_class.value} level must be in {_MIN_LEVEL}..{cap}, got {level}")
    return table[level - 1]


def level_for_xp(char_class: CharacterClass, xp: int) -> int:
    """Return the highest level attained by a character with ``xp`` experience.

    Raises ``ValueError`` if ``xp`` is negative.
    """
    if xp < 0:
        raise ValueError(f"xp must be >= 0, got {xp}")
    table = _XP_TABLE[char_class]
    level = 1
    for i, threshold in enumerate(table):
        if xp >= threshold:
            level = i + 1
    return level
