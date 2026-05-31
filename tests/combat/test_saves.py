"""Contract for OSE saving throws (M1).

Derived from docs/specs/combat.md §3 (the five save categories) and §8 behavior
5 ("Save succeeds iff d20 >= target; targets read from the class/level table"),
plus the openspec combat spec's "Saving throws" requirement. Targets are the OSE
SRD class-progression values (docs/specs/combat.md §2 names the SRD as the source
of truth). Resolution is pure and value-driven, so the d20 face is passed in
directly — no RNG seeding needed.
"""

import pytest

from world.rules.saves import CharacterClass, SaveCategory, save_succeeds, save_target

# ── resolution: d20 vs target (docs/specs/combat.md §3, §8 behavior 5) ───────


def test_save_succeeds_at_target() -> None:
    """WHEN the d20 result equals the save target THEN the save succeeds."""
    assert save_succeeds(d20=14, target=14) is True


def test_save_fails_below_target() -> None:
    """WHEN the d20 result is one under the target THEN the save fails."""
    assert save_succeeds(d20=13, target=14) is False


def test_save_succeeds_above_target() -> None:
    """WHEN the d20 result exceeds the target THEN the save succeeds."""
    assert save_succeeds(d20=20, target=14) is True


@pytest.mark.parametrize("bad", [0, 21, -1, 100])
def test_save_rejects_impossible_d20(bad: int) -> None:
    """WHEN the d20 face is outside 1..20 THEN ValueError is raised."""
    with pytest.raises(ValueError):
        save_succeeds(d20=bad, target=14)


# ── target lookup by class/level/category (OSE SRD progression tables) ───────

# (class, level, category, expected target) spot-checks against the SRD,
# covering each class, both ends of bands, and band-boundary transitions.
_TARGET_CASES = [
    # Cleric: bands 1-4 / 5-8 / 9-10.
    (CharacterClass.CLERIC, 1, SaveCategory.DEATH, 11),
    (CharacterClass.CLERIC, 4, SaveCategory.BREATH, 16),
    (CharacterClass.CLERIC, 5, SaveCategory.DEATH, 9),
    (CharacterClass.CLERIC, 9, SaveCategory.DEATH, 6),
    (CharacterClass.CLERIC, 10, SaveCategory.SPELLS, 9),
    # Fighter: bands 1-3 / 4-6 / 7-9 / 10.
    (CharacterClass.FIGHTER, 1, SaveCategory.SPELLS, 16),
    (CharacterClass.FIGHTER, 3, SaveCategory.PARALYSIS, 14),
    (CharacterClass.FIGHTER, 4, SaveCategory.SPELLS, 14),
    (CharacterClass.FIGHTER, 7, SaveCategory.BREATH, 10),
    (CharacterClass.FIGHTER, 10, SaveCategory.DEATH, 6),
    # Magic-User: bands 1-5 / 6-10. Note P (13) is better than W (14) at low level.
    (CharacterClass.MAGIC_USER, 1, SaveCategory.DEATH, 13),
    (CharacterClass.MAGIC_USER, 1, SaveCategory.PARALYSIS, 13),
    (CharacterClass.MAGIC_USER, 6, SaveCategory.DEATH, 11),
    (CharacterClass.MAGIC_USER, 10, SaveCategory.SPELLS, 12),
    # Thief: bands 1-4 / 5-8 / 9-10.
    (CharacterClass.THIEF, 1, SaveCategory.DEATH, 13),
    (CharacterClass.THIEF, 5, SaveCategory.PARALYSIS, 11),
    (CharacterClass.THIEF, 9, SaveCategory.DEATH, 10),
    (CharacterClass.THIEF, 10, SaveCategory.SPELLS, 10),
    # Dwarf: strong saves; bands 1-3 / 4-6 / 7-9 / 10.
    (CharacterClass.DWARF, 1, SaveCategory.DEATH, 8),
    (CharacterClass.DWARF, 4, SaveCategory.DEATH, 6),
    (CharacterClass.DWARF, 7, SaveCategory.DEATH, 4),
    (CharacterClass.DWARF, 10, SaveCategory.DEATH, 2),
    (CharacterClass.DWARF, 10, SaveCategory.SPELLS, 6),
    # Elf: bands 1-3 / 4-6 / 7-9 / 10.
    (CharacterClass.ELF, 1, SaveCategory.DEATH, 12),
    (CharacterClass.ELF, 4, SaveCategory.DEATH, 10),
    (CharacterClass.ELF, 7, SaveCategory.DEATH, 8),
    (CharacterClass.ELF, 10, SaveCategory.SPELLS, 8),
    # Halfling: bands 1-3 / 4-6 / 7-8 (caps at 8 in the SRD).
    (CharacterClass.HALFLING, 1, SaveCategory.DEATH, 8),
    (CharacterClass.HALFLING, 4, SaveCategory.DEATH, 6),
    (CharacterClass.HALFLING, 8, SaveCategory.BREATH, 7),
]


@pytest.mark.parametrize(("char_class", "level", "category", "expected"), _TARGET_CASES)
def test_save_target_matches_srd(
    char_class: CharacterClass, level: int, category: SaveCategory, expected: int
) -> None:
    """WHEN looking up a class/level/category THEN the target matches the SRD."""
    assert save_target(char_class=char_class, level=level, category=category) == expected


def test_save_targets_improve_with_level() -> None:
    """WHEN a class gains levels THEN its save targets never get worse (monotone)."""
    prev = 99
    for level in range(1, 11):
        target = save_target(
            char_class=CharacterClass.FIGHTER, level=level, category=SaveCategory.DEATH
        )
        assert target <= prev
        prev = target


# ── out-of-range levels (docs/specs/combat.md §2: levels 1..10, SRD caps) ────


@pytest.mark.parametrize("bad_level", [0, -1])
def test_save_target_rejects_sub_one_level(bad_level: int) -> None:
    """WHEN the level is below 1 THEN ValueError is raised."""
    with pytest.raises(ValueError):
        save_target(char_class=CharacterClass.FIGHTER, level=bad_level, category=SaveCategory.DEATH)


def test_halfling_above_srd_cap_is_rejected() -> None:
    """WHEN a Halfling exceeds its SRD level cap (8) THEN ValueError is raised."""
    # Level 8 is defined; 9 is past the Halfling's progression table.
    assert (
        save_target(char_class=CharacterClass.HALFLING, level=8, category=SaveCategory.DEATH) == 4
    )
    with pytest.raises(ValueError):
        save_target(char_class=CharacterClass.HALFLING, level=9, category=SaveCategory.DEATH)


def test_every_class_defines_all_five_categories_at_level_one() -> None:
    """WHEN any class is level 1 THEN all five categories resolve to a target."""
    for char_class in CharacterClass:
        for category in SaveCategory:
            target = save_target(char_class=char_class, level=1, category=category)
            assert 1 <= target <= 20
