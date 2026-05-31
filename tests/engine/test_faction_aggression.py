"""Engine tests for NPC faction-aggression binding and consider command (M4).

Covers docs/specs/faction.md §5 and §7 testable behavior 13:
  NPC aggression reflects standing band (friendly no-attack; KOS always-attack).
"""

from __future__ import annotations

import pytest
from evennia.utils import create

from commands.faction import CmdConsider


def _run_consider(caller: object, target_name: str) -> None:
    cmd = CmdConsider()
    cmd.caller = caller
    cmd.cmdstring = "consider"
    cmd.raw_string = f"consider {target_name}"
    cmd.args = f" {target_name}"
    cmd.parse()
    cmd.func()


# ── NPC aggression ────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_kos_mob_initiates_combat() -> None:
    """WHEN a KOS-standing player enters a room with the faction's mob THEN it attacks."""
    room = create.create_object("typeclasses.rooms.Room", key="aggro-room-kos")
    mob = create.create_object("typeclasses.npcs.Mob", key="kobold-sentry-kos", location=room)
    mob.db.faction_id = "kobold"
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="aggro-pc-kos")
    mgr = create.create_script("world.managers.faction_manager.FactionManager")
    try:
        # 10 kills → R = -30 → kill-on-sight
        for _ in range(10):
            mgr.apply_kill_member("kobold", str(char.id))
        assert mgr.standing_band("kobold", str(char.id)) == "kill-on-sight"

        messages: list[str] = []
        char.msg = lambda text, **_kw: messages.append(str(text))

        char.move_to(room, quiet=True)

        assert any("attacks" in m.lower() for m in messages)
    finally:
        mob.delete()
        if char.pk is not None:
            char.delete()
        mgr.delete()
        room.delete()


@pytest.mark.django_db
def test_friendly_mob_does_not_initiate_combat() -> None:
    """WHEN a friendly-standing player enters a room with the faction's mob THEN no attack."""
    room = create.create_object("typeclasses.rooms.Room", key="aggro-room-friendly")
    mob = create.create_object("typeclasses.npcs.Mob", key="kobold-sentry-friendly", location=room)
    mob.db.faction_id = "kobold"
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="aggro-pc-friendly")
    mgr = create.create_script("world.managers.faction_manager.FactionManager")
    try:
        # 3 quest aids → R = +30 → friendly
        for _ in range(3):
            mgr.apply_quest_aid("kobold", str(char.id))
        assert mgr.standing_band("kobold", str(char.id)) == "friendly"

        messages: list[str] = []
        char.msg = lambda text, **_kw: messages.append(str(text))

        char.move_to(room, quiet=True)

        assert not any("attacks" in m.lower() for m in messages)
    finally:
        mob.delete()
        char.delete()
        mgr.delete()
        room.delete()


@pytest.mark.django_db
def test_no_faction_mob_does_not_attack() -> None:
    """WHEN a mob has no faction_id THEN it never aggros regardless of standing."""
    room = create.create_object("typeclasses.rooms.Room", key="aggro-room-nofac")
    mob = create.create_object("typeclasses.npcs.Mob", key="wolf-nofac", location=room)
    # faction_id left as None
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="aggro-pc-nofac")
    mgr = create.create_script("world.managers.faction_manager.FactionManager")
    try:
        messages: list[str] = []
        char.msg = lambda text, **_kw: messages.append(str(text))

        char.move_to(room, quiet=True)

        assert not any("attacks" in m.lower() for m in messages)
    finally:
        mob.delete()
        char.delete()
        mgr.delete()
        room.delete()


# ── consider command ──────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_consider_kos_standing() -> None:
    """WHEN player considers a mob they are KOS with THEN message mentions kill-on-sight."""
    room = create.create_object("typeclasses.rooms.Room", key="consider-room-kos")
    mob = create.create_object("typeclasses.npcs.Mob", key="kobold-veteran-kos", location=room)
    mob.db.faction_id = "kobold"
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter", key="consider-pc-kos", location=room
    )
    mgr = create.create_script("world.managers.faction_manager.FactionManager")
    try:
        for _ in range(10):
            mgr.apply_kill_member("kobold", str(char.id))

        messages: list[str] = []
        char.msg = lambda text, **_kw: messages.append(str(text))

        _run_consider(char, mob.key)

        assert any("kill you on sight" in m.lower() for m in messages)
    finally:
        mob.delete()
        char.delete()
        mgr.delete()
        room.delete()


@pytest.mark.django_db
def test_consider_neutral_standing() -> None:
    """WHEN player considers a mob they are neutral with THEN message says indifference."""
    room = create.create_object("typeclasses.rooms.Room", key="consider-room-neutral")
    mob = create.create_object("typeclasses.npcs.Mob", key="kobold-peon-neutral", location=room)
    mob.db.faction_id = "kobold"
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter",
        key="consider-pc-neutral",
        location=room,
    )
    mgr = create.create_script("world.managers.faction_manager.FactionManager")
    try:
        messages: list[str] = []
        char.msg = lambda text, **_kw: messages.append(str(text))

        _run_consider(char, mob.key)

        assert any("indifference" in m.lower() for m in messages)
    finally:
        mob.delete()
        char.delete()
        mgr.delete()
        room.delete()


@pytest.mark.django_db
def test_consider_no_faction_target() -> None:
    """WHEN player considers a mob with no faction_id THEN told it belongs to no faction."""
    room = create.create_object("typeclasses.rooms.Room", key="consider-room-nofac")
    mob = create.create_object("typeclasses.npcs.Mob", key="wolf-nofac-cons", location=room)
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter",
        key="consider-pc-nofac",
        location=room,
    )
    try:
        messages: list[str] = []
        char.msg = lambda text, **_kw: messages.append(str(text))

        _run_consider(char, mob.key)

        assert any("no faction" in m.lower() for m in messages)
    finally:
        mob.delete()
        char.delete()
        room.delete()
