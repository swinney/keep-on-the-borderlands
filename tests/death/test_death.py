"""Tests for death & hardcore mechanics (R7 / specs/death.md §6).

Un-skipped progressively across M3 tasks:
  Task 1 (this commit): corpse creation — tests 3, 5, 6, 7, 10
  Task 2: XP loss + recall — tests 1, 2, 4
  Task 3: hardcore deletion + leaderboard — tests 8, 9
  Task 4: who-list marker — test 11
"""

from __future__ import annotations

import pytest
from evennia.utils import create

# ── M3 task 2: XP loss + recall (not yet implemented) ──────────────────────


@pytest.mark.skip(reason="M3 task 2: XP loss + recall not yet implemented")
def test_default_death_sets_xp_to_level_threshold() -> None:
    """WHEN a non-hardcore character dies THEN XP drops to the level start and level is unchanged."""


@pytest.mark.skip(reason="M3 task 2: XP loss + recall not yet implemented")
def test_default_death_with_no_progress_keeps_xp() -> None:
    """WHEN a character at the level threshold dies THEN XP is unchanged."""


# ── M3 task 1: Corpse creation ─────────────────────────────────────────────


@pytest.mark.django_db
def test_default_death_creates_corpse_with_gear_and_coin() -> None:
    """WHEN a default death occurs THEN a corpse holds all gear, inventory, and carried coin."""
    room = create.create_object("typeclasses.rooms.Room", key="dt-room-c1")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter",
        key="dt-pc-c1",
        location=room,
    )
    sword = create.create_object("typeclasses.objects.Object", key="dt-sword-c1", location=char)
    try:
        char.traits.hp.base = 5
        char.traits.hp.current = 5
        char.db.coin = 100
        char.apply_damage(5)
        corpses = [obj for obj in room.contents if "corpse" in obj.key]
        assert len(corpses) == 1
        corpse = corpses[0]
        assert sword in corpse.contents
        assert corpse.db.coin == 100
        assert (char.db.coin or 0) == 0
    finally:
        # Delete children before parents so Evennia never needs to relocate them.
        for obj in list(room.contents):
            for child in list(obj.contents):
                child.delete()
            obj.delete()
        room.delete()


# ── M3 task 2: Revive at Inner Bailey (not yet implemented) ────────────────


@pytest.mark.skip(reason="M3 task 2: recall/revive not yet implemented")
def test_default_death_revives_at_inner_bailey() -> None:
    """WHEN a default death occurs THEN the character is at the Inner Bailey at 1 HP, no spells."""


# ── M3 task 1: Looting and bank balance ────────────────────────────────────


@pytest.mark.django_db
def test_looting_corpse_restores_gear() -> None:
    """WHEN the player loots the corpse THEN gear and coin return."""
    room = create.create_object("typeclasses.rooms.Room", key="dt-room-c2")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter",
        key="dt-pc-c2",
        location=room,
    )
    sword = create.create_object("typeclasses.objects.Object", key="dt-sword-c2", location=char)
    try:
        char.traits.hp.base = 5
        char.traits.hp.current = 5
        char.db.coin = 50
        char.apply_damage(5)
        corpses = [obj for obj in room.contents if "corpse" in obj.key]
        assert len(corpses) == 1
        corpse = corpses[0]
        corpse.loot(char)
        assert sword.location == char
        assert char.db.coin == 50
        assert all("corpse" not in obj.key for obj in room.contents)
    finally:
        char.delete()
        room.delete()


@pytest.mark.django_db
def test_bank_balance_unaffected_by_death() -> None:
    """WHEN a default death occurs THEN the bank balance is unchanged and absent from the corpse."""
    room = create.create_object("typeclasses.rooms.Room", key="dt-room-c3")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter",
        key="dt-pc-c3",
        location=room,
    )
    try:
        char.traits.hp.base = 5
        char.traits.hp.current = 5
        char.db.bank_balance = 500
        char.apply_damage(5)
        assert char.db.bank_balance == 500
        corpses = [obj for obj in room.contents if "corpse" in obj.key]
        assert len(corpses) == 1
        corpse = corpses[0]
        assert (corpse.db.bank_balance or 0) == 0
    finally:
        for obj in list(room.contents):
            for child in list(obj.contents):
                child.delete()
            obj.delete()
        room.delete()


@pytest.mark.django_db
def test_default_corpse_persists_until_looted_or_reset() -> None:
    """WHEN a default corpse is created THEN it persists until looted or season reset."""
    room = create.create_object("typeclasses.rooms.Room", key="dt-room-c4")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter",
        key="dt-pc-c4",
        location=room,
    )
    try:
        char.traits.hp.base = 5
        char.traits.hp.current = 5
        char.apply_damage(5)
        corpses = [obj for obj in room.contents if "corpse" in obj.key]
        assert len(corpses) == 1
        corpse = corpses[0]
        corpse.loot(char)
        assert all("corpse" not in obj.key for obj in room.contents)
    finally:
        char.delete()
        room.delete()


# ── M3 task 3: Hardcore deletion + leaderboard (not yet implemented) ───────


@pytest.mark.skip(reason="M3 task 3: hardcore deletion not yet implemented")
def test_hardcore_death_deletes_character() -> None:
    """WHEN a hardcore character dies THEN the character is deleted and does not return."""


@pytest.mark.skip(reason="M3 task 3: leaderboard not yet implemented")
def test_hardcore_death_appends_leaderboard_entry() -> None:
    """WHEN a hardcore character dies THEN a fell entry with final level and season is appended."""


@pytest.mark.django_db
def test_hardcore_death_drops_lootable_corpse() -> None:
    """WHEN a hardcore character dies THEN a corpse lootable by others is dropped."""
    room = create.create_object("typeclasses.rooms.Room", key="dt-room-c5")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter",
        key="dt-hc-c1",
        location=room,
    )
    looter = create.create_object(
        "typeclasses.characters.PlayerCharacter",
        key="dt-looter-c1",
        location=room,
    )
    sword = create.create_object("typeclasses.objects.Object", key="dt-sword-hc", location=char)
    try:
        char.traits.hp.base = 5
        char.traits.hp.current = 5
        char.db.hardcore = True
        char.db.coin = 30
        char.apply_damage(5)
        corpses = [obj for obj in room.contents if "corpse" in obj.key]
        assert len(corpses) == 1
        corpse = corpses[0]
        assert sword in corpse.contents
        corpse.loot(looter)
        assert sword.location == looter
        assert looter.db.coin == 30
    finally:
        for obj in list(room.contents):
            for child in list(obj.contents):
                child.delete()
            obj.delete()
        room.delete()


# ── M3 task 4: Who-list marker (not yet implemented) ───────────────────────


@pytest.mark.skip(reason="M3 task 4: who-list marker not yet implemented")
def test_hardcore_flag_irrevocable_and_marked() -> None:
    """WHEN clearing the hardcore flag is attempted THEN it remains set and shows on who."""
