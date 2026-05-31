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

_D20_MIN, _D20_MAX = 1, 20


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
