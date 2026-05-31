"""Phase 0 test stubs for death & hardcore (R7).

Derived from openspec/changes/b2-mud-v1-design/specs/death-and-hardcore/spec.md
and docs/specs/death.md §6. Docstring-only; Phase 2 unskips and implements.
"""

import pytest

pytestmark = pytest.mark.skip(reason="Phase 0 stub — implementation in Phase 2")


def test_default_death_sets_xp_to_level_threshold() -> None:
    """WHEN a non-hardcore character dies THEN XP drops to the level start and level is unchanged."""


def test_default_death_with_no_progress_keeps_xp() -> None:
    """WHEN a character at the level threshold dies THEN XP is unchanged."""


def test_default_death_creates_corpse_with_gear_and_coin() -> None:
    """WHEN a default death occurs THEN a corpse holds all gear, inventory, and carried coin."""


def test_default_death_revives_at_inner_bailey() -> None:
    """WHEN a default death occurs THEN the character is at the Inner Bailey at 1 HP, no spells."""


def test_looting_corpse_restores_gear() -> None:
    """WHEN the player loots the corpse THEN gear and coin return."""


def test_bank_balance_unaffected_by_death() -> None:
    """WHEN a default death occurs THEN the bank balance is unchanged and absent from the corpse."""


def test_default_corpse_persists_until_looted_or_reset() -> None:
    """WHEN a default corpse is created THEN it persists until looted or season reset."""


def test_hardcore_death_deletes_character() -> None:
    """WHEN a hardcore character dies THEN the character is deleted and does not return."""


def test_hardcore_death_appends_leaderboard_entry() -> None:
    """WHEN a hardcore character dies THEN a fell entry with final level and season is appended."""


def test_hardcore_death_drops_lootable_corpse() -> None:
    """WHEN a hardcore character dies THEN a corpse lootable by others is dropped."""


def test_hardcore_flag_irrevocable_and_marked() -> None:
    """WHEN clearing the hardcore flag is attempted THEN it remains set and shows on who."""
