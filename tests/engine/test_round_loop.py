"""Engine tests for CombatHandler round-loop script (M2).

Verifies creation, combatant management, validity checks, and that at_repeat
runs without error.
"""

from __future__ import annotations

import pytest
from evennia.utils import create


@pytest.mark.django_db
def test_combat_handler_creation() -> None:
    handler = create.create_script("typeclasses.scripts.CombatHandler")
    try:
        assert handler.interval == 6
        assert handler.persistent is True
        assert handler.db.combatants == []
    finally:
        handler.delete()


@pytest.mark.django_db
def test_combat_handler_add_remove_combatant() -> None:
    handler = create.create_script("typeclasses.scripts.CombatHandler")
    pc = create.create_object("typeclasses.characters.PlayerCharacter", key="loop-pc")
    mob = create.create_object("typeclasses.npcs.Mob", key="loop-mob")
    try:
        handler.add_combatant(pc)
        handler.add_combatant(mob)
        assert len(handler.db.combatants) == 2
        handler.remove_combatant(pc)
        assert len(handler.db.combatants) == 1
    finally:
        handler.delete()
        pc.delete()
        mob.delete()


@pytest.mark.django_db
def test_combat_handler_is_valid_needs_two_alive() -> None:
    handler = create.create_script("typeclasses.scripts.CombatHandler")
    pc = create.create_object("typeclasses.characters.PlayerCharacter", key="valid-pc")
    mob = create.create_object("typeclasses.npcs.Mob", key="valid-mob")
    try:
        pc.traits.hp.base = 8
        mob.traits.hp.base = 6

        handler.add_combatant(pc)
        handler.add_combatant(mob)
        assert handler.is_valid() is True

        mob.traits.hp.current = 0
        assert handler.is_valid() is False
    finally:
        handler.delete()
        pc.delete()
        mob.delete()


@pytest.mark.django_db
def test_combat_handler_at_repeat_runs() -> None:
    room = create.create_object("typeclasses.rooms.Room", key="test-room")
    pc = create.create_object(
        "typeclasses.characters.PlayerCharacter", key="repeat-pc", location=room
    )
    mob = create.create_object("typeclasses.npcs.Mob", key="repeat-mob", location=room)
    handler = create.create_script("typeclasses.scripts.CombatHandler")
    try:
        pc.traits.hp.base = 8
        mob.traits.hp.base = 6

        handler.add_combatant(pc)
        handler.add_combatant(mob)
        handler.at_repeat()
    finally:
        handler.delete()
        pc.delete()
        mob.delete()
        room.delete()
