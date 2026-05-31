"""Engine tests for 0-HP death handoff stub (M2).

Verifies that apply_damage triggers at_death exactly once when HP reaches 0
for both PlayerCharacter and Mob typeclasses (combat.md §4.2, behavior 8).
"""

from __future__ import annotations

import pytest
from evennia.utils import create


@pytest.mark.django_db
def test_player_at_death_called_on_lethal_damage() -> None:
    """at_death fires exactly once when PlayerCharacter HP reaches 0."""
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="death-pc")
    try:
        char.traits.hp.base = 5
        char.traits.hp.current = 5
        called: list[bool] = []
        char.at_death = lambda: called.append(True)
        char.apply_damage(5)
        assert int(char.traits.hp.value) == 0
        assert called == [True]
    finally:
        char.delete()


@pytest.mark.django_db
def test_mob_at_death_called_on_lethal_damage() -> None:
    """at_death fires exactly once when Mob HP reaches 0."""
    mob = create.create_object("typeclasses.npcs.Mob", key="death-mob")
    try:
        mob.traits.hp.base = 4
        mob.traits.hp.current = 4
        called: list[bool] = []
        mob.at_death = lambda: called.append(True)
        mob.apply_damage(10)
        assert int(mob.traits.hp.value) == 0
        assert called == [True]
    finally:
        mob.delete()


@pytest.mark.django_db
def test_at_death_not_called_on_surviving_damage() -> None:
    """at_death does NOT fire when damage leaves HP above 0."""
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="death-pc-survive")
    try:
        char.traits.hp.base = 10
        char.traits.hp.current = 10
        called: list[bool] = []
        char.at_death = lambda: called.append(True)
        char.apply_damage(5)
        assert int(char.traits.hp.value) == 5
        assert called == []
    finally:
        char.delete()


@pytest.mark.django_db
def test_at_death_not_called_twice_on_already_dead() -> None:
    """at_death fires only once; subsequent damage to a dead combatant does not re-fire it."""
    mob = create.create_object("typeclasses.npcs.Mob", key="death-mob-twice")
    try:
        mob.traits.hp.base = 5
        mob.traits.hp.current = 5
        called: list[bool] = []
        mob.at_death = lambda: called.append(True)
        mob.apply_damage(5)
        mob.apply_damage(5)
        assert called == [True]
    finally:
        mob.delete()


@pytest.mark.django_db
def test_player_at_death_broadcasts_to_room() -> None:
    """The default PlayerCharacter at_death stub announces the death to the room."""
    room = create.create_object("typeclasses.rooms.Room", key="death-room-pc")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter", key="death-pc-room", location=room
    )
    try:
        char.traits.hp.base = 5
        char.traits.hp.current = 5
        messages: list[str] = []
        room.msg_contents = lambda text, **_kw: messages.append(str(text))
        char.apply_damage(5)
        assert any("slain" in m.lower() for m in messages)
    finally:
        # at_death creates a corpse; delete children before parents so Evennia
        # never needs to relocate them via DEFAULT_HOME.
        for obj in list(room.contents):
            for child in list(obj.contents):
                child.delete()
            obj.delete()
        # Default death recalls the character out of the room, so it is no
        # longer in room.contents — delete it explicitly to avoid leaking it.
        if char.pk is not None:
            char.delete()
        room.delete()


@pytest.mark.django_db
def test_mob_at_death_broadcasts_to_room() -> None:
    """The default Mob at_death stub announces the death to the room."""
    room = create.create_object("typeclasses.rooms.Room", key="death-room-mob")
    mob = create.create_object("typeclasses.npcs.Mob", key="death-mob-room", location=room)
    try:
        mob.traits.hp.base = 3
        mob.traits.hp.current = 3
        messages: list[str] = []
        room.msg_contents = lambda text, **_kw: messages.append(str(text))
        mob.apply_damage(3)
        assert any("slain" in m.lower() for m in messages)
    finally:
        mob.delete()
        room.delete()
