"""Goblin lair zone tests — M10 leadership-halt wiring + faction standing.

Validates that:
- The goblin tribe's chief (Snagg) and shaman (Yeek) are correctly wired to
  the M6 repop_manager (repop.md §3-4).
- Killing goblin mobs shifts the slayer's goblin faction standing (faction.md
  §2.1, §5; the M4 ↔ M10-goblin tie).

Pure-data groups run without Evennia; engine groups need pytest-django.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from typing import Any

import pytest

from world.repop import config as repop_cfg
from world.zones.caves import goblin
from world.zones.spawn_registry import spawn_points

# ---------------------------------------------------------------------------
# Group 1 — Pure-data leadership spawn verification (repop.md §3)
# ---------------------------------------------------------------------------


def test_goblin_tribe_has_exactly_one_chief_and_one_shaman() -> None:
    roles = [s.get("leader_role") for s in goblin.SPAWNS if s.get("is_leader")]
    assert roles.count("chief") == 1, "goblin tribe needs exactly one chief spawn"
    assert roles.count("shaman") == 1, "goblin tribe needs exactly one shaman spawn"


def test_goblin_leader_spawns_are_single_mobs() -> None:
    for spawn in goblin.SPAWNS:
        if spawn.get("is_leader"):
            assert spawn["count"] == 1, "a leader spawn must be a single mob"
            assert spawn.get("leader_role") in {"chief", "shaman"}


def test_goblin_derived_points_have_one_chief_and_one_shaman() -> None:
    """Leader flags survive the SpawnRecord → SpawnPoint derivation (repop.md §1)."""
    points = spawn_points("caves", goblin.SPAWNS, goblin.MOB_TEMPLATES)
    leaders = [p for p in points if p.is_leader]
    roles = [p.leader_role for p in leaders]
    assert roles.count("chief") == 1
    assert roles.count("shaman") == 1
    assert all(p.faction == "goblin" for p in leaders)


def test_goblin_designated_rival_is_gnoll() -> None:
    """The goblin tribe's rival that scouts during a halt is the gnolls (repop.md §4)."""
    assert repop_cfg.DESIGNATED_RIVAL.get("goblin") == "gnoll"


# ---------------------------------------------------------------------------
# Engine tests — chief + shaman wired to the leadership halt + rival scouting
# (repop.md §3-4)
# ---------------------------------------------------------------------------


def _goblin_leaders() -> tuple[Any, Any]:
    """Derived chief and shaman SpawnPoints for the goblin tribe."""
    points = spawn_points("caves", goblin.SPAWNS, goblin.MOB_TEMPLATES)
    chief = next(p for p in points if p.leader_role == "chief")
    shaman = next(p for p in points if p.leader_role == "shaman")
    return chief, shaman


@pytest.fixture
def repop_and_factions() -> Iterator[tuple[Any, Any]]:
    """Registered repop_manager + faction_manager, torn down after the test."""
    from evennia.utils import create  # noqa: PLC0415

    repop = create.create_script("world.managers.repop_manager.RepopManager")
    factions = create.create_script("world.managers.faction_manager.FactionManager")
    repop.register_zone("caves", goblin.SPAWNS, goblin.MOB_TEMPLATES)
    try:
        yield repop, factions
    finally:
        repop.delete()
        factions.delete()


def _make_leader_mob(spawn_id: str, key: str, room: Any) -> Any:
    from evennia.utils import create  # noqa: PLC0415

    mob = create.create_object("typeclasses.npcs.Mob", key=key, location=room)
    mob.db.spawn_id = spawn_id
    mob.db.faction_id = "goblin"
    return mob


@pytest.mark.django_db
def test_killing_one_goblin_leader_does_not_halt(
    repop_and_factions: tuple[Any, Any],
) -> None:
    """Dropping only the chief schedules its respawn but never halts the tribe."""
    from evennia.utils import create  # noqa: PLC0415

    repop, _ = repop_and_factions
    chief, _shaman = _goblin_leaders()
    room = create.create_object("typeclasses.rooms.Room", key="goblin-halt-room-1")
    try:
        chief_mob = _make_leader_mob(chief.spawn_id, "Snagg", room)
        chief_mob.at_death()
        assert chief.spawn_id in (repop.db.respawn_at or {})
        assert "goblin" not in (repop.db.halted_until or {})
        assert not (repop.db.scouts or {})
    finally:
        room.delete()


@pytest.mark.django_db
def test_killing_both_goblin_leaders_halts_and_scouts(
    repop_and_factions: tuple[Any, Any],
) -> None:
    """Chief + shaman both down → goblin repop freezes and gnoll scouts move in."""
    from evennia.utils import create  # noqa: PLC0415

    repop, factions = repop_and_factions
    chief, shaman = _goblin_leaders()
    baseline_tension = factions.get_tension("goblin", "gnoll")
    room = create.create_object("typeclasses.rooms.Room", key="goblin-halt-room-2")
    try:
        chief_mob = _make_leader_mob(chief.spawn_id, "Snagg", room)
        shaman_mob = _make_leader_mob(shaman.spawn_id, "Yeek", room)

        chief_mob.at_death()
        shaman_mob.at_death()

        # The tribe is frozen (repop.md §3).
        halted_until = (repop.db.halted_until or {}).get("goblin")
        assert halted_until is not None and halted_until > time.time()

        # The designated rival (gnoll) sends a scouting party (repop.md §4).
        scouts = repop.db.scouts or {}
        assert len(scouts) == repop_cfg.SCOUT_PARTY_SIZE
        assert all(s["faction"] == "gnoll" for s in scouts.values())
        assert all(s["scouting"] == "goblin" for s in scouts.values())

        # The halt applies the R2 leadership_broken tension spike (repop.md §3).
        assert factions.get_tension("goblin", "gnoll") > baseline_tension
    finally:
        room.delete()


# ---------------------------------------------------------------------------
# Engine tests — faction standing shifts observable in goblin behavior
# (faction.md §2.1, §5; the M4 ↔ M10-goblin tie this task delivers)
# ---------------------------------------------------------------------------


def _teardown_room(room: Any, *characters: Any) -> None:
    """Delete room contents, then the room, then any out-of-room characters."""
    for obj in list(room.contents):
        if obj.pk is not None:
            obj.delete()
    room.delete()
    for char in characters:
        if char.pk is not None:
            char.delete()


def _make_goblin_mob(room: Any, key: str = "goblin-goon", *, is_leader: bool = False) -> Any:
    from evennia.utils import create  # noqa: PLC0415

    mob = create.create_object("typeclasses.npcs.Mob", key=key, location=room)
    mob.db.faction_id = "goblin"
    mob.db.is_leader = is_leader
    return mob


@pytest.mark.django_db
def test_killing_goblin_member_lowers_player_standing(
    repop_and_factions: tuple[Any, Any],
) -> None:
    """Slaying a rank-and-file goblin drops the killer's goblin standing by kill_member."""
    from world.factions.config import STANDING_EVENTS  # noqa: PLC0415

    _, factions = repop_and_factions
    from evennia.utils import create  # noqa: PLC0415

    room = create.create_object("typeclasses.rooms.Room", key="goblin-standing-room-1")
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="goblin-slayer-1")
    try:
        assert factions.get_standing("goblin", str(char.id)) == 0
        mob = _make_goblin_mob(room)
        mob.db.last_attacker = char
        mob.at_death()
        assert factions.get_standing("goblin", str(char.id)) == STANDING_EVENTS["kill_member"]
    finally:
        _teardown_room(room, char)


@pytest.mark.django_db
def test_killing_goblin_leader_lowers_standing_more(
    repop_and_factions: tuple[Any, Any],
) -> None:
    """Chief/shaman counts extra: standing drops by the larger kill_leader hit."""
    from world.factions.config import STANDING_EVENTS  # noqa: PLC0415

    _, factions = repop_and_factions
    from evennia.utils import create  # noqa: PLC0415

    room = create.create_object("typeclasses.rooms.Room", key="goblin-standing-room-2")
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="goblin-slayer-2")
    try:
        chief = _make_goblin_mob(room, key="Snagg", is_leader=True)
        chief.db.last_attacker = char
        chief.at_death()
        assert factions.get_standing("goblin", str(char.id)) == STANDING_EVENTS["kill_leader"]
    finally:
        _teardown_room(room, char)


@pytest.mark.django_db
def test_unattributed_goblin_death_does_not_shift_standing(
    repop_and_factions: tuple[Any, Any],
) -> None:
    """A goblin dying with no recorded attacker credits no one (faction.md §2.1)."""
    _, factions = repop_and_factions
    from evennia.utils import create  # noqa: PLC0415

    room = create.create_object("typeclasses.rooms.Room", key="goblin-standing-room-3")
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="goblin-bystander")
    try:
        mob = _make_goblin_mob(room)  # last_attacker left None
        mob.at_death()
        assert factions.get_standing("goblin", str(char.id)) == 0
    finally:
        _teardown_room(room, char)
