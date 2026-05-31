"""Pure tests for world.rules.spells — spell registry and slot tables.

No Evennia/Django involved; these run in the fast pytest path.
Derived from docs/specs/combat.md §5 and §8 (behaviors 9-10).
"""

from __future__ import annotations

import pytest

from world.rules.saves import CharacterClass
from world.rules.spells import (
    SpellSchool,
    caster_school,
    get_spell,
    is_caster,
    list_spells,
    preparable_spells,
    spell_slots_for_level,
)

# ── Spell registry ─────────────────────────────────────────────────────────────


def test_light_in_registry() -> None:
    spell = get_spell("light")
    assert spell.level == 1
    assert SpellSchool.ARCANE in spell.schools
    assert SpellSchool.DIVINE in spell.schools


def test_magic_missile_in_registry() -> None:
    spell = get_spell("magic missile")
    assert spell.level == 1
    assert SpellSchool.ARCANE in spell.schools
    assert SpellSchool.DIVINE not in spell.schools


def test_cure_light_wounds_in_registry() -> None:
    spell = get_spell("cure light wounds")
    assert spell.level == 1
    assert SpellSchool.DIVINE in spell.schools
    assert SpellSchool.ARCANE not in spell.schools


def test_detect_evil_in_registry() -> None:
    spell = get_spell("detect evil")
    assert spell.level == 1
    assert SpellSchool.DIVINE in spell.schools


def test_get_spell_unknown_raises() -> None:
    with pytest.raises(KeyError):
        get_spell("fireball")


def test_list_spells_includes_all_four() -> None:
    names = {s.name for s in list_spells()}
    assert {"light", "magic missile", "cure light wounds", "detect evil"}.issubset(names)


# ── Caster class checks ────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "cls",
    [CharacterClass.MAGIC_USER, CharacterClass.CLERIC, CharacterClass.ELF],
)
def test_is_caster_true(cls: CharacterClass) -> None:
    assert is_caster(cls) is True


@pytest.mark.parametrize(
    "cls",
    [
        CharacterClass.FIGHTER,
        CharacterClass.THIEF,
        CharacterClass.DWARF,
        CharacterClass.HALFLING,
    ],
)
def test_is_caster_false(cls: CharacterClass) -> None:
    assert is_caster(cls) is False


# ── Slot table: Magic-User ─────────────────────────────────────────────────────


def test_magic_user_level_1() -> None:
    assert spell_slots_for_level(CharacterClass.MAGIC_USER, 1) == (1, 0, 0, 0, 0)


def test_magic_user_level_2() -> None:
    assert spell_slots_for_level(CharacterClass.MAGIC_USER, 2) == (2, 0, 0, 0, 0)


def test_magic_user_level_3() -> None:
    assert spell_slots_for_level(CharacterClass.MAGIC_USER, 3) == (2, 1, 0, 0, 0)


def test_magic_user_level_5() -> None:
    assert spell_slots_for_level(CharacterClass.MAGIC_USER, 5) == (2, 2, 1, 0, 0)


def test_magic_user_level_10() -> None:
    assert spell_slots_for_level(CharacterClass.MAGIC_USER, 10) == (4, 3, 3, 2, 2)


# ── Slot table: Cleric ─────────────────────────────────────────────────────────


def test_cleric_level_1_no_slots() -> None:
    assert spell_slots_for_level(CharacterClass.CLERIC, 1) == (0, 0, 0, 0, 0)


def test_cleric_level_2_first_slot() -> None:
    assert spell_slots_for_level(CharacterClass.CLERIC, 2) == (1, 0, 0, 0, 0)


def test_cleric_level_4() -> None:
    assert spell_slots_for_level(CharacterClass.CLERIC, 4) == (2, 1, 0, 0, 0)


def test_cleric_level_10() -> None:
    assert spell_slots_for_level(CharacterClass.CLERIC, 10) == (3, 3, 3, 2, 1)


# ── Slot table: Elf ────────────────────────────────────────────────────────────


def test_elf_level_1() -> None:
    assert spell_slots_for_level(CharacterClass.ELF, 1) == (1, 0, 0, 0, 0)


def test_elf_level_3() -> None:
    assert spell_slots_for_level(CharacterClass.ELF, 3) == (2, 1, 0, 0, 0)


def test_elf_level_10() -> None:
    assert spell_slots_for_level(CharacterClass.ELF, 10) == (3, 3, 3, 3, 2)


# ── Non-casters always return zero slots ────────────────────────────────────────


@pytest.mark.parametrize(
    "cls",
    [
        CharacterClass.FIGHTER,
        CharacterClass.THIEF,
        CharacterClass.DWARF,
        CharacterClass.HALFLING,
    ],
)
def test_non_caster_zero_slots(cls: CharacterClass) -> None:
    assert spell_slots_for_level(cls, 1) == (0, 0, 0, 0, 0)
    assert spell_slots_for_level(cls, 5) == (0, 0, 0, 0, 0)


# ── Invalid level inputs ───────────────────────────────────────────────────────


def test_level_zero_raises() -> None:
    with pytest.raises(ValueError):
        spell_slots_for_level(CharacterClass.MAGIC_USER, 0)


def test_level_above_cap_raises() -> None:
    with pytest.raises(ValueError):
        spell_slots_for_level(CharacterClass.MAGIC_USER, 11)


# ── School gating (combat.md §5) ───────────────────────────────────────────────


@pytest.mark.parametrize(
    ("cls", "school"),
    [
        (CharacterClass.MAGIC_USER, SpellSchool.ARCANE),
        (CharacterClass.ELF, SpellSchool.ARCANE),
        (CharacterClass.CLERIC, SpellSchool.DIVINE),
        (CharacterClass.FIGHTER, None),
        (CharacterClass.THIEF, None),
    ],
)
def test_caster_school(cls: CharacterClass, school: SpellSchool | None) -> None:
    assert caster_school(cls) == school


def test_cleric_prepares_full_divine_list_ignoring_spellbook() -> None:
    """Clerics pray: the pool is every divine spell, regardless of spellbook."""
    pool = preparable_spells(CharacterClass.CLERIC, spellbook=[])
    names = {s.name for s in pool}
    assert "cure light wounds" in names
    assert "detect evil" in names
    assert "magic missile" not in names  # arcane-only
    assert all(SpellSchool.DIVINE in s.schools for s in pool)


def test_magic_user_pool_is_arcane_spellbook_only() -> None:
    """A Magic-User prepares only arcane spells that are in their spellbook."""
    pool = preparable_spells(
        CharacterClass.MAGIC_USER, spellbook=["magic missile", "cure light wounds"]
    )
    names = {s.name for s in pool}
    assert names == {"magic missile"}  # cure light wounds is divine-only → excluded


def test_non_caster_has_empty_pool() -> None:
    assert preparable_spells(CharacterClass.FIGHTER, spellbook=["magic missile"]) == []
