"""M9 exit acceptance: the kobold-cave vertical slice, end to end.

This is the critical-integration milestone's headline test (docs/build-plan.md
M9): one run drives the whole acceptance loop across every subsystem built so
far — spawn → equip → hire a henchman → travel from the Keep through the
Wilderness into the Caves → clear the kobold tribe on a Guildmaster bounty →
return → turn the bounty in → bank the coin for XP.

Where the per-subsystem suites verify each piece in isolation (the Keep
onboarding loop in ``test_keep_onboarding``, the bounty wiring in
``tests/quests/test_guildmaster_engine``, the caves geography + leadership halt
in ``test_caves``), this suite is the integration check that they *compose* in
one live world with all three zones built and linked together. It traverses the
real exit graph across the keep↔wilderness↔caves boundaries so a break in any
inter-zone link surfaces here before M10 builds seven more caves the same way.
"""

from __future__ import annotations

import random
from collections.abc import Iterator
from typing import Any
from unittest.mock import patch

import pytest
from evennia.utils import create
from evennia.utils.search import search_object_by_tag

from commands.economy import CmdBuy
from commands.henchmen import CmdHire
from commands.quests import CmdAccept, CmdTurnin
from world.economy import grant_starting_gold, secure_treasure
from world.factions.config import STANDING_EVENTS
from world.henchmen.config import ROSTER
from world.zones import caves, keep, wilderness
from world.zones.builder import EXIT_CATEGORY, NPC_CATEGORY, ROOM_CATEGORY

CHARACTER_TYPECLASS = "typeclasses.characters.PlayerCharacter"
MOB_TYPECLASS = "typeclasses.npcs.Mob"
KOBOLD_CULL = "g_kobold_cull"
KOBOLD_CULL_COUNT = 8  # quests.md §2 / world.quests.config
BOUNTY_GP = 50

# Outbound: from the tavern (where the henchman is hired) out the Keep gate,
# across the Wilderness spine, into the Caves and down to the kobold chief's
# den. Each hop is (zone, room_key); the traversal asserts a wired exit exists.
PATH_TO_DEN: list[tuple[str, str]] = [
    ("keep", "outer_bailey"),
    ("keep", "entry_yard"),
    ("keep", "gatehouse"),
    ("keep", "main_gate"),
    ("wilderness", "keep_road"),
    ("wilderness", "crossroads"),
    ("wilderness", "river_ford"),
    ("wilderness", "hills_low"),
    ("wilderness", "raider_camp"),
    ("wilderness", "ravine_approach"),
    ("wilderness", "ravine_mouth"),
    ("caves", "ravine"),
    ("caves", "ravine_north"),
    ("caves", "kobold_mouth"),
    ("caves", "kobold_guard"),
    ("caves", "kobold_warren"),
    ("caves", "kobold_den"),
]

# Return: back out of the lair and across the Wilderness to the guildhall, where
# the bounty is turned in.
PATH_TO_GUILD: list[tuple[str, str]] = [
    ("caves", "kobold_warren"),
    ("caves", "kobold_guard"),
    ("caves", "kobold_mouth"),
    ("caves", "ravine_north"),
    ("caves", "ravine"),
    ("wilderness", "ravine_mouth"),
    ("wilderness", "ravine_approach"),
    ("wilderness", "raider_camp"),
    ("wilderness", "hills_low"),
    ("wilderness", "river_ford"),
    ("wilderness", "crossroads"),
    ("wilderness", "keep_road"),
    ("keep", "main_gate"),
    ("keep", "gatehouse"),
    ("keep", "entry_yard"),
    ("keep", "outer_bailey"),
    ("keep", "fountain_sq"),
    ("keep", "guild"),
]


def _room(zone: str, room_key: str) -> Any:
    """Resolve a built room by its ``<zone>:<key>`` identity tag."""
    matches = search_object_by_tag(f"{zone}:{room_key}", category=ROOM_CATEGORY)
    return matches[0] if matches else None


def _caves_rooms() -> list[Any]:
    return [r for r in search_object_by_tag(category=ROOM_CATEGORY) if r.db.zone == "caves"]


def _caves_exits() -> list[Any]:
    out = []
    for e in search_object_by_tag(category=EXIT_CATEGORY):
        loc = e.location
        if loc is not None and loc.db.zone == "caves":
            out.append(e)
    return out


def _run(cmd_cls: Any, caller: Any, args: str = "") -> None:
    """Execute an Evennia command against ``caller`` as the engine would."""
    cmd = cmd_cls()
    cmd.caller = caller
    cmd.cmdstring = cmd_cls.key
    cmd.raw_string = f"{cmd_cls.key} {args}".strip()
    cmd.args = f" {args}" if args else ""
    cmd.parse()
    cmd.func()


def _travel(char: Any, path: list[tuple[str, str]]) -> None:
    """Walk ``char`` along ``path``, asserting each hop is a wired exit.

    Encounters are suppressed for the duration so the integration loop stays
    deterministic (the encounter mechanic itself is covered in
    ``test_wilderness``); the henchman following is exercised for real.
    """
    with patch("world.zones.wilderness.typeclasses._random.randint", return_value=6):
        for zone, room_key in path:
            dest = _room(zone, room_key)
            assert dest is not None, f"{zone}:{room_key} was not built"
            wired = [e for e in char.location.exits if e.destination == dest]
            assert wired, (
                f"no exit from {char.location.db.zone}:{char.location.db.room_key} "
                f"to {zone}:{room_key}"
            )
            char.move_to(dest, quiet=True)
            assert char.location == dest


def _teardown_world() -> None:
    """Tear down the three built zones, NPCs and exits in a grid-safe order."""
    from evennia.contrib.grid.xyzgrid.xyzgrid import get_xyzgrid  # noqa: PLC0415

    # Caves exits (incl. the return exit) and the forward 'enter' exit, then
    # NPCs, before remove_map deletes the grid rooms their homes point at.
    for exit_ in _caves_exits():
        exit_.delete()
    for exit_ in search_object_by_tag("wilderness:ravine_mouth:enter", category=EXIT_CATEGORY):
        exit_.delete()
    for npc in search_object_by_tag(category=NPC_CATEGORY):
        npc.delete()
    get_xyzgrid().remove_map("wilderness", remove_objects=True)
    for room in _caves_rooms():
        room.delete()
    # Remaining Keep exits + rooms.
    for exit_ in search_object_by_tag(category=EXIT_CATEGORY):
        exit_.delete()
    for room in search_object_by_tag(category=ROOM_CATEGORY):
        room.delete()


def _onboard_in_keep(char: Any) -> Any:
    """Spawn, equip, accept the bounty and hire a henchman; return the henchman.

    Service visits set ``location`` directly (no movement hooks fire), so the
    rolled starting gold stays carried until the party first walks for real.
    """
    # spawn: arrive at the recall point with rolled starting gold.
    char.location = _room("keep", "inner_bailey")
    assert char.location is not None, "Inner Bailey (recall point) is built"
    char.traits.level.base = 1  # meets the bounty's min_level
    grant_starting_gold(char, random.Random(20260601))
    assert int(char.db.coin) > 0

    # equip: buy a torch at the provisioner.
    char.location = _room("keep", "provisioner")
    _run(CmdBuy, char, "torch")
    assert [o for o in char.contents if o.db.list_key == "torch"]

    # accept: take the Guildmaster's kobold bounty at the guildhall.
    char.location = _room("keep", "guild")
    _run(CmdAccept, char, "kobold")
    assert char.db.quests[KOBOLD_CULL]["state"] == "active"

    # hire: recruit the first roster henchman at the tavern.
    recruit = ROSTER[0]
    char.location = _room("keep", "tavern")
    char.traits.cha.base = 16  # comfortably above the retainer cap of 1
    with patch("commands.henchmen.dice.roll", return_value=9):
        _run(CmdHire, char, recruit.name)
    party = [o for o in char.location.contents if o.db.employer == char]
    assert len(party) == 1, "exactly one henchman joins the party"
    return party[0]


@pytest.fixture
def vertical_slice_world() -> Iterator[Any]:
    """Build Keep → Wilderness → Caves with a faction_manager; tear all down."""
    keep.build()
    wilderness.build()
    factions = create.create_script("world.managers.faction_manager.FactionManager")
    caves.build()
    try:
        yield factions
    finally:
        factions.delete()
        _teardown_world()


@pytest.mark.django_db
def test_kobold_cave_vertical_slice(vertical_slice_world: Any) -> None:
    """spawn → equip → hire → travel → clear tribe → return → turn in → bank XP."""
    factions = vertical_slice_world
    char = create.create_object(CHARACTER_TYPECLASS, key="Slice-Hero")
    henchman = None
    kobolds: list[Any] = []
    try:
        # ── spawn → equip → accept bounty → hire a henchman, all in the Keep ──
        henchman = _onboard_in_keep(char)

        # ── travel: walk the party from the Keep through the Wilderness to the
        #     kobold den, the henchman following every hop ──
        _travel(char, PATH_TO_DEN)
        assert char.location.db.room_key == "kobold_den"
        assert henchman.location == char.location, "the henchman followed into the den"

        # ── clear the tribe: 8 kobolds fall — two to the henchman's blade (credit
        #     passes to its employer, henchmen.md §4), the rest to the hero ──
        den = char.location
        standing_before = factions.get_standing("kobold", str(char.id))
        for i in range(KOBOLD_CULL_COUNT):
            mob = create.create_object(MOB_TYPECLASS, key=f"kobold-{i}", location=den)
            mob.db.faction_id = "kobold"
            mob.db.last_attacker = henchman if i < 2 else char
            kobolds.append(mob)
            mob.at_death()

        # Every kill — even the henchman's — credited the hero's bounty + standing.
        assert char.db.quests[KOBOLD_CULL]["progress"] == {"kobold": KOBOLD_CULL_COUNT}
        expected_after_kills = standing_before + KOBOLD_CULL_COUNT * STANDING_EVENTS["kill_member"]
        assert factions.get_standing("kobold", str(char.id)) == expected_after_kills
        assert factions.standing_band("kobold", str(char.id)) == "hostile"

        # ── return: travel back to the guildhall ──
        _travel(char, PATH_TO_GUILD)
        assert char.location.db.room_key == "guild"

        # ── turn in: the bounty pays its coin and applies the quest_harm shift ──
        coin_before = int(char.db.coin)
        _run(CmdTurnin, char, "kobold")
        assert char.db.quests[KOBOLD_CULL]["state"] == "complete"
        assert int(char.db.coin) == coin_before + BOUNTY_GP
        expected_after_turnin = expected_after_kills + STANDING_EVENTS["quest_harm"]
        assert factions.get_standing("kobold", str(char.id)) == expected_after_turnin
        assert factions.standing_band("kobold", str(char.id)) == "kill-on-sight"

        # ── bank for XP: securing the bounty coin in the Keep converts it 1:1 to
        #     XP (the treasure→XP-on-secure loop, economy.md §6) ──
        xp_before = int(char.traits.xp.current)
        granted = secure_treasure(char)
        assert granted == BOUNTY_GP, "the 50 gp bounty secured into 50 XP"
        assert int(char.traits.xp.current) == xp_before + BOUNTY_GP
        # The same coin never pays XP twice.
        assert secure_treasure(char) == 0
    finally:
        for mob in kobolds:
            if mob.pk is not None:
                mob.delete()
        if henchman is not None and henchman.pk is not None:
            henchman.delete()
        char.delete()
