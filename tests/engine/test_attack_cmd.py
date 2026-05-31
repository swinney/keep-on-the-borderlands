"""Engine tests for CmdAttack and TargetDummy (M2).

Verifies that the attack command correctly resolves hits/misses, applies
damage, and handles degenerate inputs. The d20 and weapon roll are patched
via unittest.mock so every branch is exercised deterministically.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from evennia.utils import create

from commands.combat import CmdAttack


# ── helpers ──────────────────────────────────────────────────────────────────


def _run_attack(caller: object, target_name: str) -> None:
    """Execute CmdAttack.func() synchronously without a live session."""
    cmd = CmdAttack()
    cmd.caller = caller
    cmd.cmdstring = "attack"
    cmd.raw_string = f"attack {target_name}"
    cmd.args = f" {target_name}"
    cmd.parse()
    cmd.func()


# ── TargetDummy ───────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_target_dummy_default_hp() -> None:
    dummy = create.create_object("typeclasses.npcs.TargetDummy", key="td-hp")
    try:
        assert dummy.traits.hp.base == 100
        assert dummy.traits.hp.value == 100
    finally:
        dummy.delete()


@pytest.mark.django_db
def test_target_dummy_is_mob() -> None:
    dummy = create.create_object("typeclasses.npcs.TargetDummy", key="td-mob")
    try:
        assert dummy.IS_MOB is True
        assert dummy.computed_ac == 10
    finally:
        dummy.delete()


# ── CmdAttack ─────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_attack_no_args_sends_usage() -> None:
    room = create.create_object("typeclasses.rooms.Room", key="atk-room-noargs")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter", key="atk-pc-noargs", location=room
    )
    try:
        messages: list[str] = []
        char.msg = lambda text, **_kw: messages.append(str(text))
        _run_attack(char, "")
        assert any("attack what" in m.lower() for m in messages)
    finally:
        char.delete()
        room.delete()


@pytest.mark.django_db
def test_attack_nat_20_always_hits() -> None:
    """Natural 20 hits regardless of target AC; damage is applied."""
    room = create.create_object("typeclasses.rooms.Room", key="atk-room-hit")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter", key="atk-pc-hit", location=room
    )
    dummy = create.create_object("typeclasses.npcs.TargetDummy", key="dummy-hit", location=room)
    try:
        char.traits.str.base = 10  # STR mod = 0
        char.traits.attack_bonus.base = 0

        mock_rng = MagicMock()
        mock_rng.randint.side_effect = [20, 4]  # d20=20 (nat 20), weapon_roll=4

        with patch("commands.combat.random.Random", return_value=mock_rng):
            _run_attack(char, dummy.key)

        # damage = max(1, 4 + 0) = 4; dummy started at 100
        assert dummy.traits.hp.value == 96
    finally:
        char.delete()
        dummy.delete()
        room.delete()


@pytest.mark.django_db
def test_attack_nat_one_always_misses() -> None:
    """Natural 1 misses regardless of bonuses; no HP is deducted."""
    room = create.create_object("typeclasses.rooms.Room", key="atk-room-miss")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter", key="atk-pc-miss", location=room
    )
    dummy = create.create_object("typeclasses.npcs.TargetDummy", key="dummy-miss", location=room)
    try:
        char.traits.str.base = 18  # STR mod = +3, but nat 1 overrides
        char.traits.attack_bonus.base = 10

        mock_rng = MagicMock()
        mock_rng.randint.side_effect = [1, 6]  # d20=1 (nat 1), weapon_roll=6 (unused)

        with patch("commands.combat.random.Random", return_value=mock_rng):
            _run_attack(char, dummy.key)

        assert dummy.traits.hp.value == 100  # untouched
    finally:
        char.delete()
        dummy.delete()
        room.delete()


@pytest.mark.django_db
def test_attack_damage_uses_str_modifier() -> None:
    """Melee damage adds the attacker's STR modifier."""
    room = create.create_object("typeclasses.rooms.Room", key="atk-room-str")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter", key="atk-pc-str", location=room
    )
    dummy = create.create_object("typeclasses.npcs.TargetDummy", key="dummy-str", location=room)
    try:
        char.traits.str.base = 16  # STR mod = +2
        char.traits.attack_bonus.base = 0

        mock_rng = MagicMock()
        mock_rng.randint.side_effect = [20, 3]  # nat 20 hits; weapon_roll=3

        with patch("commands.combat.random.Random", return_value=mock_rng):
            _run_attack(char, dummy.key)

        # damage = max(1, 3 + 2) = 5; dummy started at 100
        assert dummy.traits.hp.value == 95
    finally:
        char.delete()
        dummy.delete()
        room.delete()


@pytest.mark.django_db
def test_attack_self_rejected() -> None:
    room = create.create_object("typeclasses.rooms.Room", key="atk-room-self")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter", key="atk-pc-self", location=room
    )
    try:
        messages: list[str] = []
        char.msg = lambda text, **_kw: messages.append(str(text))
        _run_attack(char, char.key)
        assert any("can't attack yourself" in m.lower() for m in messages)
    finally:
        char.delete()
        room.delete()
