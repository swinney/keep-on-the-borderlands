"""Contract for ascending-AC attack math (M1).

Derived from docs/specs/combat.md §3 (armor class), §4.1 (attack resolution and
damage) and §8 behaviors 2-4, plus the openspec combat spec's attack/damage
scenarios. Resolution is pure and value-driven, so the d20 face and weapon-die
total are passed in directly — no RNG seeding needed.
"""

import pytest

from world.rules import combat

# ── ascending armor class (docs/specs/combat.md §3, behavior 2) ──────────────


def test_ascending_ac_sums_parts() -> None:
    """WHEN DEX +1, leather +2, shield +1 THEN AC is 14."""
    assert combat.armor_class(dex_modifier=1, armor_bonus=2, shield_bonus=1) == 14


def test_ac_unarmored_is_ten_plus_dex() -> None:
    """WHEN no armor or shield THEN AC is 10 + DEX modifier."""
    assert combat.armor_class(dex_modifier=0) == 10
    assert combat.armor_class(dex_modifier=-2) == 8
    assert combat.armor_class(dex_modifier=3) == 13


# ── attack resolution (docs/specs/combat.md §4.1, behavior 3) ────────────────


def test_attack_hits_at_target_ac() -> None:
    """WHEN the modified attack total equals the target AC THEN the attack hits."""
    # 15 + 1 + 1 = 17 against AC 17 — meets the AC.
    assert combat.attack_hits(d20=15, attack_bonus=1, ability_modifier=1, target_ac=17) is True


def test_attack_misses_just_below_target_ac() -> None:
    """WHEN the modified total is one under the target AC THEN the attack misses."""
    # 14 + 1 + 1 = 16 against AC 17.
    assert combat.attack_hits(d20=14, attack_bonus=1, ability_modifier=1, target_ac=17) is False


def test_situational_modifier_can_turn_a_miss_into_a_hit() -> None:
    """WHEN a situational bonus lifts the total to the AC THEN the attack hits."""
    # 14 + 1 + 1 = 16 misses AC 17; a +1 situational bonus reaches it.
    assert combat.attack_hits(d20=14, attack_bonus=1, ability_modifier=1, target_ac=17) is False
    assert (
        combat.attack_hits(d20=14, attack_bonus=1, ability_modifier=1, target_ac=17, situational=1)
        is True
    )


def test_natural_twenty_always_hits() -> None:
    """WHEN the d20 is a natural 20 THEN the attack hits regardless of AC."""
    # Even a hopeless total (20 - 10 - 10 = 0) against a sky-high AC connects.
    assert combat.attack_hits(d20=20, attack_bonus=-10, ability_modifier=-10, target_ac=99) is True


def test_natural_one_always_misses() -> None:
    """WHEN the d20 is a natural 1 THEN the attack misses regardless of total."""
    # A huge bonus that would otherwise meet AC 1 still misses on a nat 1.
    assert combat.attack_hits(d20=1, attack_bonus=50, ability_modifier=50, target_ac=1) is False


@pytest.mark.parametrize("bad", [0, 21, -1, 100])
def test_attack_rejects_impossible_d20(bad: int) -> None:
    """WHEN the d20 face is outside 1..20 THEN ValueError is raised."""
    with pytest.raises(ValueError):
        combat.attack_hits(d20=bad, attack_bonus=0, ability_modifier=0, target_ac=10)


# ── damage application (docs/specs/combat.md §4.1, behavior 4) ───────────────


def test_melee_damage_adds_str() -> None:
    """WHEN resolving melee damage THEN the STR modifier is added to the weapon roll."""
    assert combat.melee_damage(weapon_roll=6, str_modifier=2) == 8


def test_missile_damage_ignores_str() -> None:
    """WHEN resolving missile damage THEN no STR modifier is added."""
    assert combat.missile_damage(weapon_roll=6) == 6


def test_melee_damage_floors_at_one() -> None:
    """WHEN weapon roll plus a negative STR modifier is below 1 THEN damage is 1."""
    assert combat.melee_damage(weapon_roll=1, str_modifier=-3) == 1


def test_missile_damage_floors_at_one() -> None:
    """WHEN a (hypothetical) missile roll is below 1 THEN damage floors at 1."""
    assert combat.missile_damage(weapon_roll=0) == 1
