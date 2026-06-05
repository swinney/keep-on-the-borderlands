"""Combat scenarios not owned by a focused rules test file.

The rules-level scenarios from the Phase-0 stub (ability modifier, ascending
AC, attack edges, damage, saves, HP, morale) now live in dedicated test files
— `test_abilities`, `test_attack`, `test_saves`, `test_progression`,
`test_morale`. The assertion-free copies were removed from here: unskipping the
module had made them "pass" vacuously, a false green. What remains is the
initiative-ordering helper, the death predicate, and explicit skips for
behaviours owned by later milestones.
"""

import pytest

from world.rules.combat import initiative_order, is_dead
from world.rules.spells import SpellDeclaration


def test_individual_initiative_orders_actors() -> None:
    """WHEN two combatants roll 1d6+DEX THEN the higher total acts first."""
    entries = [("A", 1, 4), ("B", 0, 3)]
    result = initiative_order(entries)
    assert result[0][0] == "A"
    assert result[1][0] == "B"

    # Tie-break by DEX: both total 5 but A has higher DEX modifier.
    tie_entries = [("A", 2, 3), ("B", 1, 4)]
    tie_result = initiative_order(tie_entries)
    assert tie_result[0][0] == "A"


def test_zero_hp_is_dead() -> None:
    """WHEN a combatant reaches 0 HP THEN it is dead and leaves initiative (§4.2)."""
    assert is_dead(0) is True
    assert is_dead(-1) is True
    assert is_dead(1) is False
    assert is_dead(100) is False


@pytest.mark.skip(reason="slot consumption covered by tests/engine/test_spells.py")
def test_casting_consumes_slot() -> None:
    """WHEN a caster casts a prepared spell THEN that slot is expended."""


def test_damage_disrupts_unresolved_cast() -> None:
    """WHEN a caster takes damage before resolution THEN the spell fails and slot is lost.

    Pure declare→resolve core (combat.md §4.1, §5): a fresh declaration resolves
    at end of round, but a disruption (damage taken in the interim) stops it.
    The engine wires this through ``db.spell_declaring`` / ``apply_damage`` /
    ``CombatHandler`` (covered in ``tests/engine/test_spells.py``).
    """
    declaration = SpellDeclaration("magic missile")
    # Undisturbed, the spell resolves at the end of the round.
    assert declaration.resolves() is True

    # A faster attacker lands a blow before resolution → the cast is spoiled.
    declaration.disrupt()
    assert declaration.disrupted is True
    assert declaration.resolves() is False


@pytest.mark.skip(reason="M7 — character creation")
def test_class_selection_gated_by_prime_requisite() -> None:
    """WHEN a class's prime-req minimum is unmet THEN that class is not selectable."""


@pytest.mark.skip(reason="M3 — death & hardcore")
def test_hardcore_opt_in_is_irrevocable() -> None:
    """WHEN a player confirms hardcore at creation THEN the flag is permanent."""
