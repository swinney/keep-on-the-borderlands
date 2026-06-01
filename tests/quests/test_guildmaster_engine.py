"""Engine tests for the M9 Guildmaster bounty slice (docs/specs/quests.md §2, §9).

Boots Django/Evennia (pytest-django) to verify the live wiring the pure tests
can't: the Guildmaster stands in the guildhall, the room-scoped accept/turn-in
commands drive the state machine, kobold deaths credit quest progress through
``Mob.at_death``, the reward pays coin and applies the kobold standing hit, and
that bounty coin converts to XP through the treasure→XP-on-secure loop.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from evennia.utils import create
from evennia.utils.search import search_object_by_tag

from commands.quests import CmdAccept, CmdTurnin
from world.economy import secure_treasure
from world.factions.config import STANDING_EVENTS
from world.zones import keep
from world.zones.builder import EXIT_CATEGORY, NPC_CATEGORY, ROOM_CATEGORY, find_npc

KOBOLD_CULL = "g_kobold_cull"


def _keep_rooms() -> list[Any]:
    return list(search_object_by_tag(category=ROOM_CATEGORY))


@pytest.fixture
def built_keep_with_factions() -> Iterator[Any]:
    """Build the Keep and register a faction_manager; tear both down after."""
    keep.build()
    factions = create.create_script("world.managers.faction_manager.FactionManager")
    try:
        yield factions
    finally:
        factions.delete()
        for npc in search_object_by_tag(category=NPC_CATEGORY):
            npc.delete()
        for exit_ in search_object_by_tag(category=EXIT_CATEGORY):
            exit_.delete()
        for room in _keep_rooms():
            room.delete()


def _guild_room() -> Any:
    matches = search_object_by_tag("keep:guild", category=ROOM_CATEGORY)
    return matches[0] if matches else None


def _run(cmd_cls: type, caller: Any, args: str) -> None:
    """Instantiate, parse and run a Command the way the engine would."""
    cmd = cmd_cls()
    cmd.caller = caller
    cmd.args = f" {args}"
    cmd.parse()
    cmd.func()


def _make_player(room: Any, key: str) -> Any:
    return create.create_object("typeclasses.characters.PlayerCharacter", key=key, location=room)


def _slay_kobolds(player: Any, room: Any, count: int) -> None:
    """Spawn ``count`` kobolds attributed to ``player`` and kill them one by one."""
    for i in range(count):
        mob = create.create_object("typeclasses.npcs.Mob", key=f"kobold-{i}", location=room)
        mob.db.faction_id = "kobold"
        mob.db.last_attacker = player
        mob.at_death()


def _teardown(room: Any, *chars: Any) -> None:
    for obj in list(room.contents):
        if obj.pk is not None:
            obj.delete()
    room.delete()
    for char in chars:
        if char.pk is not None:
            char.delete()


@pytest.mark.django_db
def test_guildmaster_stands_in_the_guildhall(built_keep_with_factions: Any) -> None:
    guildmaster = find_npc("keep", "guildmaster")
    assert guildmaster is not None
    assert guildmaster.location.db.room_key == "guild"
    assert getattr(guildmaster, "IS_SERVICE_NPC", False)


@pytest.mark.django_db
def test_kobold_deaths_credit_quest_progress(built_keep_with_factions: Any) -> None:
    guild = _guild_room()
    player = _make_player(guild, "bounty-hunter-1")
    pen = create.create_object("typeclasses.rooms.Room", key="kobold-pen-1")
    try:
        _run(CmdAccept, player, "kobold")
        assert player.db.quests[KOBOLD_CULL]["state"] == "active"
        _slay_kobolds(player, pen, 3)
        assert player.db.quests[KOBOLD_CULL]["progress"] == {"kobold": 3}
    finally:
        _teardown(pen, player)


@pytest.mark.django_db
def test_cannot_turn_in_before_steps_met(built_keep_with_factions: Any) -> None:
    guild = _guild_room()
    player = _make_player(guild, "bounty-hunter-2")
    pen = create.create_object("typeclasses.rooms.Room", key="kobold-pen-2")
    try:
        _run(CmdAccept, player, "kobold")
        _slay_kobolds(player, pen, 5)  # short of the 8 required
        _run(CmdTurnin, player, "kobold")
        # Still active (not turned in), no coin paid.
        assert player.db.quests[KOBOLD_CULL]["state"] == "active"
        assert int(player.db.coin or 0) == 0
    finally:
        _teardown(pen, player)


@pytest.mark.django_db
def test_turn_in_pays_gp_and_lowers_kobold_standing(built_keep_with_factions: Any) -> None:
    factions = built_keep_with_factions
    guild = _guild_room()
    player = _make_player(guild, "bounty-hunter-3")
    pen = create.create_object("typeclasses.rooms.Room", key="kobold-pen-3")
    try:
        _run(CmdAccept, player, "kobold")
        _slay_kobolds(player, pen, 8)
        coin_before = int(player.db.coin or 0)
        standing_before = factions.get_standing("kobold", str(player.id))

        _run(CmdTurnin, player, "kobold")

        assert player.db.quests[KOBOLD_CULL]["state"] == "complete"
        assert int(player.db.coin or 0) == coin_before + 50
        # The completion applies the R2 quest_harm standing shift on top of the
        # per-kill drops already booked by the eight kobold deaths.
        expected = standing_before + STANDING_EVENTS["quest_harm"]
        assert factions.get_standing("kobold", str(player.id)) == expected
    finally:
        _teardown(pen, player)


@pytest.mark.django_db
def test_bounty_coin_secures_into_xp(built_keep_with_factions: Any) -> None:
    """The headline M9 loop: bounty gp, secured in the Keep, becomes XP (economy.md §6)."""
    guild = _guild_room()
    player = _make_player(guild, "bounty-hunter-4")
    pen = create.create_object("typeclasses.rooms.Room", key="kobold-pen-4")
    try:
        _run(CmdAccept, player, "kobold")
        _slay_kobolds(player, pen, 8)
        _run(CmdTurnin, player, "kobold")
        assert int(player.db.coin or 0) == 50
        assert int(player.traits.xp.current) == 0

        # Securing the carried coin in a Keep room converts it 1 gp → 1 XP.
        granted = secure_treasure(player)
        assert granted == 50
        assert int(player.traits.xp.current) == 50

        # Re-securing the same coin grants nothing further.
        assert secure_treasure(player) == 0
        assert int(player.traits.xp.current) == 50
    finally:
        _teardown(pen, player)
