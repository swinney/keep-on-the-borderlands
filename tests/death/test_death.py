"""Tests for death & hardcore mechanics (R7 / specs/death.md §6).

Un-skipped progressively across M3 tasks:
  Task 1 (this commit): corpse creation — tests 3, 5, 6, 7, 10
  Task 2: XP loss + recall — tests 1, 2, 4
  Task 3: hardcore deletion + leaderboard — tests 8, 9
  Task 4: who-list marker — test 11
"""

from __future__ import annotations

import pytest
from evennia.objects.models import ObjectDB
from evennia.server.models import ServerConfig
from evennia.utils import create

from world.leaderboard import get_fell_entries
from world.rules.progression import xp_for_level
from world.rules.saves import CharacterClass

# ── M3 task 2: XP loss + recall ────────────────────────────────────────────


@pytest.mark.django_db
def test_default_death_sets_xp_to_level_threshold() -> None:
    """WHEN a non-hardcore character dies THEN XP drops to the level start and level is unchanged."""
    room = create.create_object("typeclasses.rooms.Room", key="dt-room-xp1")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter",
        key="dt-pc-xp1",
        location=room,
    )
    try:
        char.db.char_class = CharacterClass.FIGHTER
        char.traits.level.base = 3
        char.traits.xp.current = 5000  # above Fighter level-3 threshold (4000)
        char.traits.hp.base = 5
        char.traits.hp.current = 5
        char.apply_damage(5)
        threshold = xp_for_level(CharacterClass.FIGHTER, 3)
        assert int(char.traits.xp.current) == threshold
        assert int(char.traits.level.value) == 3
    finally:
        char.delete()
        for obj in list(room.contents):
            for child in list(obj.contents):
                child.delete()
            obj.delete()
        room.delete()


@pytest.mark.django_db
def test_default_death_with_no_progress_keeps_xp() -> None:
    """WHEN a character at the level threshold dies THEN XP is unchanged."""
    room = create.create_object("typeclasses.rooms.Room", key="dt-room-xp2")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter",
        key="dt-pc-xp2",
        location=room,
    )
    try:
        char.db.char_class = CharacterClass.FIGHTER
        char.traits.level.base = 3
        threshold = xp_for_level(CharacterClass.FIGHTER, 3)  # 4000
        char.traits.xp.current = threshold  # exactly at level start
        char.traits.hp.base = 5
        char.traits.hp.current = 5
        char.apply_damage(5)
        assert int(char.traits.xp.current) == threshold
    finally:
        char.delete()
        for obj in list(room.contents):
            for child in list(obj.contents):
                child.delete()
            obj.delete()
        room.delete()


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


# ── M3 task 2: Revive at Inner Bailey ──────────────────────────────────────


@pytest.mark.django_db
def test_default_death_revives_at_inner_bailey() -> None:
    """WHEN a default death occurs THEN the character is at the Inner Bailey at 1 HP, no spells."""
    death_room = create.create_object("typeclasses.rooms.Room", key="dt-room-ib1")
    inner_bailey = create.create_object("typeclasses.rooms.Room", key="dt-inner-bailey")
    inner_bailey.tags.add("inner_bailey")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter",
        key="dt-pc-ib1",
        location=death_room,
    )
    try:
        char.traits.hp.base = 5
        char.traits.hp.current = 5
        char.db.memorized_spells = ["light"]
        char.apply_damage(5)
        assert char.location == inner_bailey
        assert int(char.traits.hp.current) == 1
        assert char.db.memorized_spells == []
    finally:
        char.delete()
        for obj in list(death_room.contents):
            for child in list(obj.contents):
                child.delete()
            obj.delete()
        death_room.delete()
        inner_bailey.delete()


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


@pytest.mark.django_db
def test_hardcore_death_deletes_character() -> None:
    """WHEN a hardcore character dies THEN the character is deleted and does not return."""
    room = create.create_object("typeclasses.rooms.Room", key="dt-room-hd1")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter",
        key="dt-hc-del1",
        location=room,
    )
    char_pk = char.pk
    try:
        char.traits.hp.base = 5
        char.traits.hp.current = 5
        char.db.hardcore = True
        char.apply_damage(5)
        assert not ObjectDB.objects.filter(pk=char_pk).exists()
    finally:
        for obj in list(room.contents):
            for child in list(obj.contents):
                child.delete()
            obj.delete()
        room.delete()


@pytest.mark.django_db
def test_hardcore_death_appends_leaderboard_entry() -> None:
    """WHEN a hardcore character dies THEN a fell entry with final level and season is appended."""
    ServerConfig.objects.conf("leaderboard_fell", delete=True)

    room = create.create_object("typeclasses.rooms.Room", key="dt-room-lb1")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter",
        key="dt-hc-lb1",
        location=room,
    )
    try:
        char.db.char_class = CharacterClass.FIGHTER
        char.traits.level.base = 5
        char.traits.hp.base = 5
        char.traits.hp.current = 5
        char.db.hardcore = True
        char.apply_damage(5)
        entries = get_fell_entries()
        assert len(entries) >= 1
        entry = entries[-1]
        assert entry["name"] == "dt-hc-lb1"
        assert entry["level"] == 5
        assert "season" in entry
        assert "class" in entry
    finally:
        ServerConfig.objects.conf("leaderboard_fell", delete=True)
        for obj in list(room.contents):
            for child in list(obj.contents):
                child.delete()
            obj.delete()
        room.delete()


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


@pytest.mark.django_db
def test_hardcore_flag_irrevocable_and_marked() -> None:
    """WHEN clearing the hardcore flag is attempted THEN it remains set and shows on who."""
    room = create.create_object("typeclasses.rooms.Room", key="dt-room-hcvis")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter",
        key="dt-hc-vis",
        location=room,
    )
    normal = create.create_object(
        "typeclasses.characters.PlayerCharacter",
        key="dt-normal-vis",
        location=room,
    )
    try:
        char.enable_hardcore()
        assert char.hardcore is True

        # Irrevocable (death.md §4): the flag may be turned on at creation but
        # no setter path clears it — an attempt to set it False is ignored.
        char.hardcore = False
        assert char.hardcore is True

        # Who-list / title marker present for hardcore, absent for normal.
        assert "[HC]" in char.get_display_name(char)
        assert "[HC]" not in normal.get_display_name(normal)
    finally:
        for obj in list(room.contents):
            obj.delete()
        room.delete()
