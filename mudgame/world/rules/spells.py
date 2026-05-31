"""Vancian spell rules: spell registry and slot tables (pure, Evennia-free).

docs/specs/combat.md §5: memorization-on-rest, one slot consumed per cast,
interruption on damage, effects via immediate resolution.  All data here is
pure; the engine-layer commands (commands/spells.py) apply effects.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from world.rules.saves import CharacterClass


class SpellSchool(Enum):
    ARCANE = "arcane"
    DIVINE = "divine"


@dataclass(frozen=True)
class SpellData:
    name: str
    schools: frozenset[SpellSchool]
    level: int  # spell level 1-5
    description: str


# ── Spell registry ─────────────────────────────────────────────────────────────
# B2-prioritised v1 spells (combat.md §5).  Detect Evil is load-bearing for the
# disguised-priest detection path (specs/disguised-priest.md).

_SPELL_LIST: list[SpellData] = [
    SpellData(
        name="light",
        schools=frozenset({SpellSchool.ARCANE, SpellSchool.DIVINE}),
        level=1,
        description=(
            "Creates magical light (torchlight strength) at the caster's location "
            "for 12 turns per caster level."
        ),
    ),
    SpellData(
        name="magic missile",
        schools=frozenset({SpellSchool.ARCANE}),
        level=1,
        description=(
            "Unerring bolt of magical force: 1d6+1 damage to one target. "
            "No attack roll; always hits."
        ),
    ),
    SpellData(
        name="cure light wounds",
        schools=frozenset({SpellSchool.DIVINE}),
        level=1,
        description="Restores 1d6+1 hit points to one living creature.",
    ),
    SpellData(
        name="detect evil",
        schools=frozenset({SpellSchool.DIVINE}),
        level=1,
        description=(
            "Reveals evil creatures or objects within 60 feet for 12 turns. "
            "Load-bearing for the disguised-priest detection path."
        ),
    ),
]

_REGISTRY: dict[str, SpellData] = {s.name: s for s in _SPELL_LIST}


def get_spell(name: str) -> SpellData:
    """Return the SpellData for ``name``.

    Raises :exc:`KeyError` if the spell is not in the registry.
    """
    return _REGISTRY[name]


def list_spells() -> list[SpellData]:
    """Return all registered spells in definition order."""
    return list(_SPELL_LIST)


# ── Spell-slot tables (OSE SRD) ────────────────────────────────────────────────
# Index [character_level - 1] → (slots_L1, slots_L2, slots_L3, slots_L4, slots_L5).
# Character levels 1-10 (B2-scaled cap, CLAUDE.md §2).
# Non-casters (Fighter, Thief, Dwarf, Halfling) have no entry; they return zeros.

_SLOTS: dict[CharacterClass, tuple[tuple[int, int, int, int, int], ...]] = {
    CharacterClass.MAGIC_USER: (
        (1, 0, 0, 0, 0),  # level 1
        (2, 0, 0, 0, 0),  # level 2
        (2, 1, 0, 0, 0),  # level 3
        (2, 2, 0, 0, 0),  # level 4
        (2, 2, 1, 0, 0),  # level 5
        (2, 2, 1, 1, 0),  # level 6
        (3, 2, 2, 1, 0),  # level 7
        (3, 3, 2, 2, 0),  # level 8
        (3, 3, 3, 2, 1),  # level 9
        (4, 3, 3, 2, 2),  # level 10
    ),
    CharacterClass.CLERIC: (
        (0, 0, 0, 0, 0),  # level 1 — Clerics gain spells from level 2
        (1, 0, 0, 0, 0),  # level 2
        (2, 0, 0, 0, 0),  # level 3
        (2, 1, 0, 0, 0),  # level 4
        (2, 2, 0, 0, 0),  # level 5
        (2, 2, 1, 0, 0),  # level 6
        (2, 2, 1, 1, 0),  # level 7
        (3, 2, 2, 1, 0),  # level 8
        (3, 3, 2, 2, 0),  # level 9
        (3, 3, 3, 2, 1),  # level 10
    ),
    CharacterClass.ELF: (
        (1, 0, 0, 0, 0),  # level 1
        (2, 0, 0, 0, 0),  # level 2
        (2, 1, 0, 0, 0),  # level 3
        (2, 2, 0, 0, 0),  # level 4
        (2, 2, 1, 0, 0),  # level 5
        (2, 2, 1, 1, 0),  # level 6
        (3, 2, 2, 1, 0),  # level 7
        (3, 3, 2, 2, 0),  # level 8
        (3, 3, 3, 2, 0),  # level 9
        (3, 3, 3, 3, 2),  # level 10
    ),
}

_CASTER_CLASSES: frozenset[CharacterClass] = frozenset(_SLOTS.keys())

_ZERO_SLOTS: tuple[int, int, int, int, int] = (0, 0, 0, 0, 0)

# Which spell school each caster class draws from (OSE). Magic-User/Elf are
# arcane; Cleric is divine. Non-casters draw from neither.
_ARCANE_CLASSES: frozenset[CharacterClass] = frozenset(
    {CharacterClass.MAGIC_USER, CharacterClass.ELF}
)
_DIVINE_CLASSES: frozenset[CharacterClass] = frozenset({CharacterClass.CLERIC})


def is_caster(char_class: CharacterClass) -> bool:
    """Return True if ``char_class`` can memorize and cast spells."""
    return char_class in _CASTER_CLASSES


def caster_school(char_class: CharacterClass) -> SpellSchool | None:
    """Return the spell school a class casts from, or None for non-casters."""
    if char_class in _ARCANE_CLASSES:
        return SpellSchool.ARCANE
    if char_class in _DIVINE_CLASSES:
        return SpellSchool.DIVINE
    return None


def preparable_spells(char_class: CharacterClass, spellbook: list[str]) -> list[SpellData]:
    """Spells ``char_class`` may prepare on rest, gated by school (combat.md §5).

    Divine casters (Cleric) pray from the **full divine list** — no spellbook
    needed. Arcane casters (Magic-User, Elf) prepare from their ``spellbook``,
    restricted to spells of their school. This prevents e.g. a Magic-User
    preparing ``cure light wounds`` or a Cleric preparing ``magic missile``.
    """
    school = caster_school(char_class)
    if school is None:
        return []
    if school is SpellSchool.DIVINE:
        return [s for s in _SPELL_LIST if SpellSchool.DIVINE in s.schools]
    return [
        _REGISTRY[name]
        for name in spellbook
        if name in _REGISTRY and SpellSchool.ARCANE in _REGISTRY[name].schools
    ]


def spell_slots_for_level(
    char_class: CharacterClass, character_level: int
) -> tuple[int, int, int, int, int]:
    """Return the (L1, L2, L3, L4, L5) slot counts for the given class and level.

    Non-caster classes always return ``(0, 0, 0, 0, 0)``.

    Raises :exc:`ValueError` for ``character_level < 1`` or above the class cap.
    """
    if character_level < 1:
        raise ValueError(f"character_level must be >= 1, got {character_level}")
    if char_class not in _SLOTS:
        return _ZERO_SLOTS
    table = _SLOTS[char_class]
    cap = len(table)
    if character_level > cap:
        raise ValueError(
            f"{char_class.value} has no spell table above level {cap}, got {character_level}"
        )
    return table[character_level - 1]
