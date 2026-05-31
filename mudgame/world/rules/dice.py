"""Dice notation parsing and rolling (pure, Evennia-free).

OSE expresses every random outcome as ``NdM(+K)`` — N dice of M sides plus an
optional signed modifier (e.g. ``1d20``, ``3d6``, ``1d8-1``). This module turns
those strings into results.

Testability seam (ADR 0004): rolling takes an injected ``random.Random`` so
tests seed it for fully reproducible results. Downstream *resolution* (attack
hits, saves) is kept pure and value-driven elsewhere — it consumes the integers
this module produces rather than rolling itself.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass

# count (optional → 1), 'd', sides, optional signed modifier.
_NOTATION = re.compile(r"(\d*)d(\d+)([+-]\d+)?")


@dataclass(frozen=True, slots=True)
class DiceRoll:
    """A parsed dice expression: ``count`` dice of ``sides`` sides, plus ``modifier``."""

    count: int
    sides: int
    modifier: int = 0


def parse(notation: str) -> DiceRoll:
    """Parse an ``NdM(+K)`` dice string into a :class:`DiceRoll`.

    Examples (see tests/combat/test_dice.py for the full contract):
        ``"1d20"`` → ``DiceRoll(1, 20, 0)``
        ``"d6"``   → ``DiceRoll(1, 6, 0)``   (count defaults to 1)
        ``"3d6+2"``→ ``DiceRoll(3, 6, 2)``
        ``"1d8-1"``→ ``DiceRoll(1, 8, -1)``

    Tolerates surrounding/interior whitespace and an upper- or lower-case ``d``.
    Raises ``ValueError`` on anything malformed — empty string, missing/zero
    count or sides, a dangling sign, or non-dice junk.
    """
    match = _NOTATION.fullmatch("".join(notation.lower().split()))
    if match is None:
        raise ValueError(f"malformed dice notation: {notation!r}")
    count_text, sides_text, modifier_text = match.groups()
    count = int(count_text) if count_text else 1
    sides = int(sides_text)
    if count < 1 or sides < 1:
        raise ValueError(f"dice count and sides must be >= 1: {notation!r}")
    return DiceRoll(count=count, sides=sides, modifier=int(modifier_text or 0))


def roll_dice(count: int, sides: int, rng: random.Random) -> list[int]:
    """Roll ``count`` dice of ``sides`` sides, returning each die's value."""
    return [rng.randint(1, sides) for _ in range(count)]


def roll(notation: str, *, rng: random.Random) -> int:
    """Parse ``notation`` and return the summed total plus modifier."""
    expr = parse(notation)
    return sum(roll_dice(expr.count, expr.sides, rng)) + expr.modifier
