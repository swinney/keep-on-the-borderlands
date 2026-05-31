"""Engine tests for Vancian spells: CmdCast, CmdRest, spell effects (M2).

Covers combat.md §5 and §8 behaviors 9 (memorization fills slots; casting
consumes slot) and 10 (damage before resolution disrupts the declared spell).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from evennia.utils import create

from commands.spells import CmdCast, CmdRest

# ── Command helpers ────────────────────────────────────────────────────────────


def _run_cast(caller: object, args: str) -> None:
    cmd = CmdCast()
    cmd.caller = caller
    cmd.cmdstring = "cast"
    cmd.raw_string = f"cast {args}"
    cmd.args = f" {args}"
    cmd.parse()
    cmd.func()


def _run_rest(caller: object) -> None:
    cmd = CmdRest()
    cmd.caller = caller
    cmd.cmdstring = "rest"
    cmd.raw_string = "rest"
    cmd.args = ""
    cmd.parse()
    cmd.func()


# ── Memorization (CmdRest) ─────────────────────────────────────────────────────


@pytest.mark.django_db
def test_rest_fills_slots_magic_user() -> None:
    """Magic-User L1 gets 1 first-level slot from their spellbook."""
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="rest-mu")
    try:
        char.db.char_class = "magic_user"
        char.traits.level.base = 1
        char.db.spellbook = ["magic missile"]

        _run_rest(char)

        assert char.db.memorized_spells == ["magic missile"]
    finally:
        char.delete()


@pytest.mark.django_db
def test_rest_fills_two_slots_magic_user_level2() -> None:
    """Magic-User L2 gets 2 first-level slots; same spell memorized twice."""
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="rest-mu2")
    try:
        char.db.char_class = "magic_user"
        char.traits.level.base = 2
        char.db.spellbook = ["light"]

        _run_rest(char)

        assert char.db.memorized_spells == ["light", "light"]
    finally:
        char.delete()


@pytest.mark.django_db
def test_rest_cleric_level1_no_slots() -> None:
    """Cleric at level 1 has zero spell slots — nothing is memorized."""
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="rest-cl1")
    try:
        char.db.char_class = "cleric"
        char.traits.level.base = 1
        char.db.spellbook = ["cure light wounds"]

        _run_rest(char)

        assert char.db.memorized_spells == []
    finally:
        char.delete()


@pytest.mark.django_db
def test_rest_cleric_level2_gets_one_slot() -> None:
    """Cleric at level 2 gains 1 first-level slot."""
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="rest-cl2")
    try:
        char.db.char_class = "cleric"
        char.traits.level.base = 2
        char.db.spellbook = ["cure light wounds"]

        _run_rest(char)

        assert char.db.memorized_spells == ["cure light wounds"]
    finally:
        char.delete()


@pytest.mark.django_db
def test_rest_non_caster_no_spells() -> None:
    """Fighters have no spell slots; rest sends a simple recovery message."""
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="rest-ftr")
    try:
        char.db.char_class = "fighter"
        char.db.spellbook = []

        messages: list[str] = []
        char.msg = lambda text, **_kw: messages.append(str(text))

        _run_rest(char)

        assert any("rest" in m.lower() for m in messages)
        assert char.db.memorized_spells == []
    finally:
        char.delete()


# ── CmdCast: slot consumption ──────────────────────────────────────────────────


@pytest.mark.django_db
def test_cast_consumes_memorized_slot() -> None:
    """Casting a spell removes it from the memorized list."""
    room = create.create_object("typeclasses.rooms.Room", key="cast-room-consume")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter", key="cast-pc-consume", location=room
    )
    try:
        char.db.memorized_spells = ["light"]

        _run_cast(char, "light")

        assert "light" not in (char.db.memorized_spells or [])
    finally:
        char.delete()
        room.delete()


@pytest.mark.django_db
def test_cast_without_memorized_spell_fails() -> None:
    """Attempting to cast a spell not in the memorized list sends an error."""
    room = create.create_object("typeclasses.rooms.Room", key="cast-room-nomem")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter", key="cast-pc-nomem", location=room
    )
    try:
        char.db.memorized_spells = []

        messages: list[str] = []
        char.msg = lambda text, **_kw: messages.append(str(text))

        _run_cast(char, "light")

        assert any("not memorized" in m.lower() for m in messages)
    finally:
        char.delete()
        room.delete()


@pytest.mark.django_db
def test_cast_unknown_spell_fails() -> None:
    room = create.create_object("typeclasses.rooms.Room", key="cast-room-unk")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter", key="cast-pc-unk", location=room
    )
    try:
        messages: list[str] = []
        char.msg = lambda text, **_kw: messages.append(str(text))

        _run_cast(char, "fireball")

        assert any("unknown spell" in m.lower() for m in messages)
    finally:
        char.delete()
        room.delete()


# ── CmdCast: spell effects ─────────────────────────────────────────────────────


@pytest.mark.django_db
def test_cast_light_broadcasts_message() -> None:
    """Casting light sends a message to everyone in the room."""
    room = create.create_object("typeclasses.rooms.Room", key="cast-room-light")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter", key="cast-pc-light", location=room
    )
    try:
        char.db.memorized_spells = ["light"]

        messages: list[str] = []
        room.msg_contents = lambda text, **_kw: messages.append(str(text))

        _run_cast(char, "light")

        assert any("light" in m.lower() for m in messages)
        assert room.db.light_spell is True
    finally:
        char.delete()
        room.delete()


@pytest.mark.django_db
def test_cast_magic_missile_deals_damage() -> None:
    """Magic missile always hits and deals 1d6+1 damage."""
    room = create.create_object("typeclasses.rooms.Room", key="cast-room-mm")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter", key="cast-pc-mm", location=room
    )
    dummy = create.create_object("typeclasses.npcs.TargetDummy", key="cast-dummy-mm", location=room)
    try:
        char.db.memorized_spells = ["magic missile"]

        mock_rng = MagicMock()
        mock_rng.randint.return_value = 4  # d6 = 4 → damage = 4+1 = 5

        with patch("commands.spells.random.Random", return_value=mock_rng):
            _run_cast(char, "magic missile cast-dummy-mm")

        assert dummy.traits.hp.value == 95  # 100 - 5
    finally:
        char.delete()
        dummy.delete()
        room.delete()


@pytest.mark.django_db
def test_cast_magic_missile_no_target_fails() -> None:
    """Magic missile without a target sends an error."""
    room = create.create_object("typeclasses.rooms.Room", key="cast-room-mm-nt")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter", key="cast-pc-mm-nt", location=room
    )
    try:
        char.db.memorized_spells = ["magic missile"]

        messages: list[str] = []
        char.msg = lambda text, **_kw: messages.append(str(text))

        _run_cast(char, "magic missile")

        assert any("whom" in m.lower() or "target" in m.lower() for m in messages)
    finally:
        char.delete()
        room.delete()


@pytest.mark.django_db
def test_cast_cure_light_wounds_heals_target() -> None:
    """Cure light wounds restores 1d6+1 HP to the target."""
    room = create.create_object("typeclasses.rooms.Room", key="cast-room-clw")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter", key="cast-pc-clw", location=room
    )
    try:
        char.db.memorized_spells = ["cure light wounds"]
        char.traits.hp.base = 20
        char.traits.hp.current = 10  # wounded

        mock_rng = MagicMock()
        mock_rng.randint.return_value = 5  # d6 = 5 → heal = 5+1 = 6

        with patch("commands.spells.random.Random", return_value=mock_rng):
            _run_cast(char, "cure light wounds me")

        assert int(char.traits.hp.value) == 16  # 10 + 6
    finally:
        char.delete()
        room.delete()


@pytest.mark.django_db
def test_cast_cure_light_wounds_caps_at_max() -> None:
    """Cure light wounds does not raise HP above the maximum."""
    room = create.create_object("typeclasses.rooms.Room", key="cast-room-clw-cap")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter", key="cast-pc-clw-cap", location=room
    )
    try:
        char.db.memorized_spells = ["cure light wounds"]
        char.traits.hp.base = 8
        char.traits.hp.current = 7  # nearly full

        mock_rng = MagicMock()
        mock_rng.randint.return_value = 6  # d6 = 6 → heal = 7

        with patch("commands.spells.random.Random", return_value=mock_rng):
            _run_cast(char, "cure light wounds me")

        assert int(char.traits.hp.value) == 8  # capped at max
    finally:
        char.delete()
        room.delete()


@pytest.mark.django_db
def test_cast_detect_evil_finds_evil_creature() -> None:
    """Detect evil reports creatures with IS_EVIL or db.is_evil set."""
    room = create.create_object("typeclasses.rooms.Room", key="cast-room-de")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter", key="cast-pc-de", location=room
    )
    mob = create.create_object("typeclasses.npcs.Mob", key="dark-priest", location=room)
    try:
        char.db.memorized_spells = ["detect evil"]
        mob.db.is_evil = True

        messages: list[str] = []
        char.msg = lambda text, **_kw: messages.append(str(text))

        _run_cast(char, "detect evil")

        assert any("dark-priest" in m for m in messages)
        assert any("evil" in m.lower() for m in messages)
    finally:
        char.delete()
        mob.delete()
        room.delete()


@pytest.mark.django_db
def test_cast_detect_evil_empty_room() -> None:
    """Detect evil in a clean room reports no evil presence."""
    room = create.create_object("typeclasses.rooms.Room", key="cast-room-de-empty")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter", key="cast-pc-de-empty", location=room
    )
    try:
        char.db.memorized_spells = ["detect evil"]

        messages: list[str] = []
        char.msg = lambda text, **_kw: messages.append(str(text))

        _run_cast(char, "detect evil")

        assert any("no evil" in m.lower() for m in messages)
    finally:
        char.delete()
        room.delete()


# ── Disruption (combat.md §5, §8 behavior 10) ─────────────────────────────────


@pytest.mark.django_db
def test_damage_while_declaring_disrupts_spell() -> None:
    """Taking damage with db.spell_declaring set consumes the slot without effect.

    This simulates a faster attacker hitting the caster in the same round before
    the spell resolves.  The round-loop integration that sets spell_declaring will
    arrive in a later milestone; here we test the disruption mechanic directly.
    """
    room = create.create_object("typeclasses.rooms.Room", key="cast-room-disrupt")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter", key="cast-pc-disrupt", location=room
    )
    try:
        char.traits.hp.base = 20
        char.db.memorized_spells = ["magic missile"]
        char.db.spell_declaring = "magic missile"

        messages: list[str] = []
        char.msg = lambda text, **_kw: messages.append(str(text))

        char.apply_damage(3)

        # Slot was consumed (disrupted, not cast)
        assert "magic missile" not in (char.db.memorized_spells or [])
        # Disruption flag is set
        assert char.db.spell_disrupted is True
        # Disruption message was sent
        assert any("disrupted" in m.lower() for m in messages)
    finally:
        char.delete()
        room.delete()


@pytest.mark.django_db
def test_damage_without_declaring_does_not_disrupt() -> None:
    """Damage with no spell declaring does not set the disrupted flag."""
    room = create.create_object("typeclasses.rooms.Room", key="cast-room-nodisrupt")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter", key="cast-pc-nodisrupt", location=room
    )
    try:
        char.traits.hp.base = 20
        char.db.memorized_spells = ["light"]
        char.db.spell_declaring = None
        char.db.spell_disrupted = False

        char.apply_damage(2)

        assert char.db.spell_disrupted is False
        assert "light" in (char.db.memorized_spells or [])
    finally:
        char.delete()
        room.delete()
