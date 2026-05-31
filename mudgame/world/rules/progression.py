"""Character advancement: hit points now; XP thresholds and level lookup later.

docs/specs/combat.md §3: HP gained per level is the class hit die plus the CON
modifier, with a floor of 1 so a bad roll or a negative CON never costs a level.
"""

from __future__ import annotations

import random


def roll_hit_points(*, hit_die: int, con_modifier: int, rng: random.Random) -> int:
    """Roll one level's hit points: ``max(1, 1dHIT_DIE + con_modifier)``."""
    return max(1, rng.randint(1, hit_die) + con_modifier)
