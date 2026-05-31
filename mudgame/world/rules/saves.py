"""OSE saving throws: the five save categories by class and level (pure).

docs/specs/combat.md §3: five OSE save categories — Death/Poison, Wands,
Paralysis/Petrify, Breath, Spells/Rods/Staves. A save succeeds when
``d20 >= save_target(char_class, level, category)`` (§8 behavior 5). Targets are
the class/level progression values from the **OSE SRD** — the source of truth
per docs/specs/combat.md §2 — written out explicitly rather than computed so
each band can be eyeballed against the book.

Levels run 1..10 (the B2-scaled range, CLAUDE.md §2). The demi-human
race-classes cap below 10 in the SRD (Halfling at 8); a lookup above a class's
defined range raises ``ValueError`` rather than inventing a value the rules do
not define.

Testability seam (ADR 0004, mirrored from combat.py): resolution is **pure and
value-driven** — ``save_succeeds`` consumes the d20 face the caller already
rolled via ``world.rules.dice`` rather than rolling itself, so the boundary
(meeting the target) and the failure branch both test deterministically without
seeding.
"""

from __future__ import annotations

from enum import Enum

_D20_MIN, _D20_MAX = 1, 20
_MIN_LEVEL = 1


class SaveCategory(Enum):
    """The five OSE saving-throw categories (docs/specs/combat.md §3)."""

    DEATH = "death_poison"
    WANDS = "wands"
    PARALYSIS = "paralysis_petrify"
    BREATH = "breath"
    SPELLS = "spells_rods_staves"


class CharacterClass(Enum):
    """The four classes plus three race-as-classes (CLAUDE.md §2)."""

    CLERIC = "cleric"
    FIGHTER = "fighter"
    MAGIC_USER = "magic_user"
    THIEF = "thief"
    DWARF = "dwarf"
    ELF = "elf"
    HALFLING = "halfling"


# Position of each category within a band's five-value tuple below.
_CATEGORY_INDEX: dict[SaveCategory, int] = {
    SaveCategory.DEATH: 0,
    SaveCategory.WANDS: 1,
    SaveCategory.PARALYSIS: 2,
    SaveCategory.BREATH: 3,
    SaveCategory.SPELLS: 4,
}

# OSE SRD class progression tables, expressed as level bands. Each entry is
# ``(highest_level_in_band, (D, W, P, B, S))`` in ascending level order, where
# the five values follow _CATEGORY_INDEX. Bands are truncated at the B2-scaled
# level cap of 10 (or the class's lower SRD cap, e.g. Halfling at 8).
_SAVE_BANDS: dict[CharacterClass, tuple[tuple[int, tuple[int, int, int, int, int]], ...]] = {
    CharacterClass.CLERIC: (
        (4, (11, 12, 14, 16, 15)),
        (8, (9, 10, 12, 14, 12)),
        (10, (6, 7, 9, 11, 9)),
    ),
    CharacterClass.FIGHTER: (
        (3, (12, 13, 14, 15, 16)),
        (6, (10, 11, 12, 13, 14)),
        (9, (8, 9, 10, 10, 12)),
        (10, (6, 7, 8, 8, 10)),
    ),
    CharacterClass.MAGIC_USER: (
        (5, (13, 14, 13, 16, 15)),
        (10, (11, 12, 11, 14, 12)),
    ),
    CharacterClass.THIEF: (
        (4, (13, 14, 13, 16, 15)),
        (8, (12, 13, 11, 14, 13)),
        (10, (10, 11, 9, 12, 10)),
    ),
    CharacterClass.DWARF: (
        (3, (8, 9, 10, 13, 12)),
        (6, (6, 7, 8, 10, 10)),
        (9, (4, 5, 6, 7, 8)),
        (10, (2, 3, 4, 4, 6)),
    ),
    CharacterClass.ELF: (
        (3, (12, 13, 13, 15, 15)),
        (6, (10, 11, 11, 13, 12)),
        (9, (8, 9, 9, 10, 10)),
        (10, (6, 7, 8, 8, 8)),
    ),
    CharacterClass.HALFLING: (
        (3, (8, 9, 10, 13, 12)),
        (6, (6, 7, 8, 10, 10)),
        (8, (4, 5, 6, 7, 8)),
    ),
}


def save_target(*, char_class: CharacterClass, level: int, category: SaveCategory) -> int:
    """Return the OSE save target for a ``char_class``/``level``/``category`` (§3).

    A save succeeds on ``d20 >= save_target(...)`` (see :func:`save_succeeds`).
    Lower targets are better — they improve as the character gains levels.

    Raises ``ValueError`` if ``level`` is below 1 or above the class's defined
    SRD range (e.g. a Halfling above level 8).
    """
    if level < _MIN_LEVEL:
        raise ValueError(f"character level must be >= {_MIN_LEVEL}, got {level}")
    bands = _SAVE_BANDS[char_class]
    for highest_level, values in bands:
        if level <= highest_level:
            return values[_CATEGORY_INDEX[category]]
    cap = bands[-1][0]
    raise ValueError(f"{char_class.value} has no save table above level {cap}, got {level}")


def save_succeeds(*, d20: int, target: int) -> bool:
    """Resolve a save: it succeeds when ``d20 >= target`` (§3, §8 behavior 5).

    ``d20`` is the already-rolled face (1..20) from ``world.rules.dice``;
    ``target`` comes from :func:`save_target`. Meeting the target succeeds.

    Raises ``ValueError`` if ``d20`` is outside ``1..20``.
    """
    if not _D20_MIN <= d20 <= _D20_MAX:
        raise ValueError(f"d20 face must be in 1..20, got {d20}")
    return d20 >= target
