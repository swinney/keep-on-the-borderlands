"""Engine tests for PlayerCharacter and Mob typeclasses (M2).

Verifies that traits are wired at creation time, that computed_ac applies the
OSE DEX modifier, and that apply_damage reduces HP and floors at zero.
"""

from __future__ import annotations

import pytest
from evennia.utils import create


@pytest.mark.django_db
def test_character_traits_wired() -> None:
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="test-pc")
    try:
        assert char.traits.str is not None
        assert char.traits.dex is not None
        assert char.traits.con is not None
        assert char.traits.hp is not None
        assert char.traits.ac is not None
        assert char.traits.level is not None
    finally:
        char.delete()


@pytest.mark.django_db
def test_character_default_values() -> None:
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="test-pc-defaults")
    try:
        assert char.traits.str.base == 10
        assert char.traits.dex.base == 10
        assert char.traits.con.base == 10
        assert char.traits.hp.base == 1
        assert char.traits.ac.base == 10
        assert char.traits.level.base == 1
    finally:
        char.delete()


@pytest.mark.django_db
def test_character_computed_ac_dex_10() -> None:
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="test-pc-ac10")
    try:
        char.traits.dex.base = 10
        assert char.computed_ac == 10
    finally:
        char.delete()


@pytest.mark.django_db
def test_character_computed_ac_dex_13() -> None:
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="test-pc-ac11")
    try:
        char.traits.dex.base = 13
        assert char.computed_ac == 11
    finally:
        char.delete()


@pytest.mark.django_db
def test_character_apply_damage_reduces_hp() -> None:
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="test-pc-dmg")
    try:
        char.traits.hp.base = 8
        del char.traits.hp.current
        char.apply_damage(3)
        assert char.traits.hp.value == 5
    finally:
        char.delete()


@pytest.mark.django_db
def test_character_lethal_damage_revives_to_one_hp() -> None:
    # Damage floors HP at 0 internally; at_death() then revives the (non-hardcore)
    # character to 1 HP at recall (M3), so the observable post-death HP is 1.
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="test-pc-floor")
    try:
        char.traits.hp.base = 4
        del char.traits.hp.current
        char.apply_damage(999)
        assert char.traits.hp.value == 1
    finally:
        char.delete()


@pytest.mark.django_db
def test_mob_traits_wired() -> None:
    mob = create.create_object("typeclasses.npcs.Mob", key="test-mob")
    try:
        assert mob.traits.str is not None
        assert mob.traits.dex is not None
        assert mob.traits.con is not None
        assert mob.traits.hp is not None
        assert mob.traits.ac is not None
        assert mob.traits.level is not None
        assert mob.traits.morale is not None
    finally:
        mob.delete()


@pytest.mark.django_db
def test_mob_is_mob_flag() -> None:
    mob = create.create_object("typeclasses.npcs.Mob", key="test-mob-flag")
    try:
        assert mob.IS_MOB is True
    finally:
        mob.delete()


@pytest.mark.django_db
def test_mob_computed_ac_dex_10() -> None:
    mob = create.create_object("typeclasses.npcs.Mob", key="test-mob-ac")
    try:
        mob.traits.dex.base = 10
        assert mob.computed_ac == 10
    finally:
        mob.delete()


@pytest.mark.django_db
def test_mob_apply_damage_reduces_hp() -> None:
    mob = create.create_object("typeclasses.npcs.Mob", key="test-mob-dmg")
    try:
        mob.traits.hp.base = 6
        del mob.traits.hp.current
        mob.apply_damage(2)
        assert mob.traits.hp.value == 4
    finally:
        mob.delete()
