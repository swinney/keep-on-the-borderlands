"""Ascending-AC attack math: to-hit, nat-20/nat-1 edges, damage (pure).

docs/specs/combat.md §3 (armor class) and §4.1 (attack resolution / damage).
Locked convention: **ascending AC**, higher is better, hit when the modified
attack total meets or beats the target's AC.

Testability seam (ADR 0004, mirrored from dice.py): resolution here is **pure
and value-driven** — it consumes the integers ``dice.roll`` produces (the d20
face, the weapon-die total) rather than rolling itself. Callers roll via
``world.rules.dice`` and pass the results in, so every branch — including the
natural-20/natural-1 edges — is exercised deterministically without seeding.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

_D20_MIN, _D20_MAX = 1, 20
_D6_MIN, _D6_MAX = 1, 6


def armor_class(*, dex_modifier: int, armor_bonus: int = 0, shield_bonus: int = 0) -> int:
    """Ascending AC = ``10 + DEX modifier + worn armor + shield`` (§3).

    The armor and shield bonuses come from equipped gear (the ``clothing``
    contrib at the engine layer); here they are plain integers so the formula
    stays pure and testable. Higher AC is harder to hit.
    """
    return 10 + dex_modifier + armor_bonus + shield_bonus


def attack_hits(
    *,
    d20: int,
    attack_bonus: int,
    ability_modifier: int,
    target_ac: int,
    situational: int = 0,
) -> bool:
    """Resolve one attack against an ascending ``target_ac`` (§4.1).

    The hit total is ``d20 + attack_bonus + ability_modifier + situational``;
    the attack hits when it is ``>= target_ac``. ``ability_modifier`` is the
    attacker's STR for melee or DEX for missile (the caller chooses which to
    pass). ``attack_bonus`` is the ascending value (``20 - THAC0``) read from
    the class/level table.

    Edges (adopted for clean, testable behavior): a **natural 20 always hits**
    and a **natural 1 always misses**, regardless of the modified total.

    Raises ``ValueError`` if ``d20`` is outside ``1..20``.
    """
    if not _D20_MIN <= d20 <= _D20_MAX:
        raise ValueError(f"d20 face must be in 1..20, got {d20}")
    if d20 == _D20_MAX:
        return True
    if d20 == _D20_MIN:
        return False
    return d20 + attack_bonus + ability_modifier + situational >= target_ac


def melee_damage(*, weapon_roll: int, str_modifier: int) -> int:
    """Melee damage: ``max(1, weapon_roll + STR modifier)`` (§4.1).

    ``weapon_roll`` is the already-rolled weapon-die total. STR modifier is
    added (a negative one can drag a small roll below 1), then floored at 1 so
    a connecting blow always deals at least a point.
    """
    return max(1, weapon_roll + str_modifier)


def missile_damage(*, weapon_roll: int) -> int:
    """Missile damage: ``max(1, weapon_roll)`` — no STR modifier (§4.1)."""
    return max(1, weapon_roll)


def initiative_roll(*, dex_modifier: int, d6: int) -> int:
    """Individual initiative: ``d6 + DEX modifier`` (§4, spec combat.md).

    Raises ``ValueError`` if ``d6`` is outside ``1..6``.
    """
    if not _D6_MIN <= d6 <= _D6_MAX:
        raise ValueError(f"d6 face must be in 1..6, got {d6}")
    return d6 + dex_modifier


def initiative_order(
    entries: Sequence[tuple[Any, int, int]],
) -> list[tuple[Any, int, int]]:
    """Sort combatants by descending initiative total, tie-broken by descending DEX.

    Each entry is ``(combatant, dex_modifier, d6_roll)``. Returns a new list
    ordered highest-initiative-first. Ties in the summed total are resolved by
    the raw DEX modifier (higher DEX acts earlier); remaining ties are left in
    stable input order so the caller can apply a coin-flip if desired.
    """
    return sorted(entries, key=lambda e: (-(e[2] + e[1]), -e[1]))


def is_dead(current_hp: int) -> bool:
    """Return True when a combatant is at or below 0 HP (§4.2, no bleed-out in v1)."""
    return current_hp <= 0


_2D6_MIN, _2D6_MAX = 2, 12


def morale_holds(*, dice_total: int, morale_score: int) -> bool:
    """Resolve a morale check: holds when ``dice_total <= morale_score`` (§6).

    ``dice_total`` is the already-rolled 2d6 total; ``morale_score`` is the
    creature or henchman rating (typically 6-12 per OSE). Meeting the score
    holds morale; exceeding it means the group routs.

    Raises ``ValueError`` if ``dice_total`` is outside the 2d6 range (2..12).
    """
    if not _2D6_MIN <= dice_total <= _2D6_MAX:
        raise ValueError(f"2d6 total must be in 2..12, got {dice_total}")
    return dice_total <= morale_score
