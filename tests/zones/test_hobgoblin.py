"""Hobgoblin lair zone tests (Cave E).

Derived from docs/specs/zones/caves.md §Cave E, docs/specs/repop.md §3-4, and
docs/specs/faction.md §2.1 / §5. Pure-data groups validate static room/mob/spawn
data without booting Evennia; engine groups (pytest-django) verify the leadership
halt, rival scouting, and faction standing wiring.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from typing import Any

import pytest

from world.factions.config import FACTIONS, STANDING_EVENTS
from world.repop import config as repop_cfg
from world.zones.caves import discovery, hobgoblin
from world.zones.spawn_registry import spawn_points

HOBGOBLIN_LAIR_ROOMS: frozenset[str] = frozenset(
    {
        "hobgoblin_gate",
        "hobgoblin_hall",
        "hobgoblin_barracks",
        "hobgoblin_mess",
        "hobgoblin_quarters",
        "hobgoblin_inner",
        "hobgoblin_armory",
        "hobgoblin_shaman",
        "hobgoblin_guard",
        "hobgoblin_throne",
    }
)


# ---------------------------------------------------------------------------
# Group 1 — Standard tribe interface
# ---------------------------------------------------------------------------


def test_tribe_exposes_standard_interface() -> None:
    assert callable(hobgoblin.build)
    assert isinstance(hobgoblin.ROOMS, list)
    assert isinstance(hobgoblin.EXITS, list)
    assert isinstance(hobgoblin.MOB_TEMPLATES, list)
    assert isinstance(hobgoblin.SPAWNS, list)
    assert isinstance(hobgoblin.NPCS, list)


# ---------------------------------------------------------------------------
# Group 2 — Room / exit data integrity (zones spec §6: 2, 8)
# ---------------------------------------------------------------------------


def test_expected_rooms_present() -> None:
    keys = {r["key"] for r in hobgoblin.ROOMS}
    assert keys >= HOBGOBLIN_LAIR_ROOMS


def test_room_keys_unique() -> None:
    keys = [r["key"] for r in hobgoblin.ROOMS]
    assert len(keys) == len(set(keys))


def test_all_lair_rooms_are_dark() -> None:
    by_key = {r["key"]: r for r in hobgoblin.ROOMS}
    for key in HOBGOBLIN_LAIR_ROOMS:
        assert by_key[key].get("dark") is True, f"{key} should be dark"


# ---------------------------------------------------------------------------
# Group 3 — Mob templates (zones spec §6: 3, 9)
# ---------------------------------------------------------------------------


def test_all_mobs_use_hobgoblin_faction() -> None:
    assert all(m["faction"] == "hobgoblin" for m in hobgoblin.MOB_TEMPLATES)


def test_hobgoblin_faction_is_valid() -> None:
    assert "hobgoblin" in FACTIONS


def test_mob_ascending_ac_in_range() -> None:
    for mob in hobgoblin.MOB_TEMPLATES:
        assert mob["ac"] >= 10, f"mob {mob['key']!r} AC {mob['ac']} below ascending base 10"


def test_mob_keys_unique() -> None:
    keys = [m["key"] for m in hobgoblin.MOB_TEMPLATES]
    assert len(keys) == len(set(keys))


# ---------------------------------------------------------------------------
# Group 4 — Spawns + leadership (zones spec §6: 4, 5)
# ---------------------------------------------------------------------------


def test_spawn_templates_are_defined() -> None:
    mob_keys = {m["key"] for m in hobgoblin.MOB_TEMPLATES}
    for spawn in hobgoblin.SPAWNS:
        assert spawn["template"] in mob_keys, (
            f"spawn in {spawn['room']!r} references unknown template {spawn['template']!r}"
        )


def test_spawn_rooms_are_lair_rooms() -> None:
    for spawn in hobgoblin.SPAWNS:
        assert spawn["room"] in HOBGOBLIN_LAIR_ROOMS, (
            f"spawn references room {spawn['room']!r} outside the hobgoblin lair"
        )


def test_hobgoblin_tribe_has_exactly_one_chief_and_one_shaman() -> None:
    roles = [s.get("leader_role") for s in hobgoblin.SPAWNS if s.get("is_leader")]
    assert roles.count("chief") == 1, "hobgoblin needs exactly one chief spawn (King Nardo)"
    assert roles.count("shaman") == 1, "hobgoblin needs exactly one shaman spawn (Vurt)"


def test_leader_spawns_are_single_and_well_formed() -> None:
    for spawn in hobgoblin.SPAWNS:
        if spawn.get("is_leader"):
            assert spawn.get("leader_role") in {"chief", "shaman"}
            assert spawn["count"] == 1, "a leader spawn must be a single mob"


# ---------------------------------------------------------------------------
# Group 5 — Repop spawn-point derivation (repop.md §1; pure, no Evennia)
# ---------------------------------------------------------------------------


def test_spawn_points_expand_count() -> None:
    """Each individual mob becomes its own SpawnPoint (per-mob respawn, §2)."""
    points = spawn_points("caves", hobgoblin.SPAWNS, hobgoblin.MOB_TEMPLATES)
    assert len(points) == sum(s["count"] for s in hobgoblin.SPAWNS)


def test_spawn_point_ids_are_unique() -> None:
    points = spawn_points("caves", hobgoblin.SPAWNS, hobgoblin.MOB_TEMPLATES)
    ids = [p.spawn_id for p in points]
    assert len(ids) == len(set(ids))


def test_derived_points_have_one_chief_and_one_shaman_leader() -> None:
    """The two hobgoblin leaders the R3 halt depends on survive derivation."""
    points = spawn_points("caves", hobgoblin.SPAWNS, hobgoblin.MOB_TEMPLATES)
    leaders = [p for p in points if p.is_leader]
    roles = [p.leader_role for p in leaders]
    assert roles.count("chief") == 1
    assert roles.count("shaman") == 1
    assert all(p.faction == "hobgoblin" for p in leaders)


def test_designated_rival_is_goblin() -> None:
    """When hobgoblin leadership breaks, goblin scouts move in (repop.md §4)."""
    assert repop_cfg.DESIGNATED_RIVAL.get("hobgoblin") == "goblin"


# ---------------------------------------------------------------------------
# Engine tests — leadership halt + rival scouting (repop.md §3-4)
# ---------------------------------------------------------------------------


def _hobgoblin_leaders() -> tuple[Any, Any]:
    """The derived chief and shaman SpawnPoints for the hobgoblin tribe."""
    points = spawn_points("caves", hobgoblin.SPAWNS, hobgoblin.MOB_TEMPLATES)
    chief = next(p for p in points if p.faction == "hobgoblin" and p.leader_role == "chief")
    shaman = next(p for p in points if p.faction == "hobgoblin" and p.leader_role == "shaman")
    return chief, shaman


@pytest.fixture
def repop_and_factions() -> Iterator[tuple[Any, Any]]:
    """A registered repop_manager + faction_manager, torn down after the test."""
    from evennia.utils import create  # noqa: PLC0415

    repop = create.create_script("world.managers.repop_manager.RepopManager")
    factions = create.create_script("world.managers.faction_manager.FactionManager")
    repop.register_zone("caves", hobgoblin.SPAWNS, hobgoblin.MOB_TEMPLATES)
    try:
        yield repop, factions
    finally:
        repop.delete()
        factions.delete()


def _make_leader_mob(spawn_id: str, key: str, room: Any) -> Any:
    from evennia.utils import create  # noqa: PLC0415

    mob = create.create_object("typeclasses.npcs.Mob", key=key, location=room)
    mob.db.spawn_id = spawn_id
    mob.db.faction_id = "hobgoblin"
    return mob


@pytest.mark.django_db
def test_killing_one_hobgoblin_leader_does_not_halt(
    repop_and_factions: tuple[Any, Any],
) -> None:
    """Dropping only the king schedules its respawn but never halts the tribe."""
    from evennia.utils import create  # noqa: PLC0415

    repop, _ = repop_and_factions
    chief, _shaman = _hobgoblin_leaders()
    room = create.create_object("typeclasses.rooms.Room", key="hobgoblin-halt-room-1")
    try:
        chief_mob = _make_leader_mob(chief.spawn_id, "King Nardo", room)
        chief_mob.at_death()
        assert chief.spawn_id in (repop.db.respawn_at or {})
        assert "hobgoblin" not in (repop.db.halted_until or {})
        assert not (repop.db.scouts or {})
    finally:
        room.delete()


@pytest.mark.django_db
def test_killing_both_hobgoblin_leaders_halts_and_scouts(
    repop_and_factions: tuple[Any, Any],
) -> None:
    """King Nardo + Vurt both down → hobgoblin repop freezes and goblin scouts move in."""
    from evennia.utils import create  # noqa: PLC0415

    repop, factions = repop_and_factions
    chief, shaman = _hobgoblin_leaders()
    baseline_tension = factions.get_tension("hobgoblin", "goblin")
    room = create.create_object("typeclasses.rooms.Room", key="hobgoblin-halt-room-2")
    try:
        chief_mob = _make_leader_mob(chief.spawn_id, "King Nardo", room)
        shaman_mob = _make_leader_mob(shaman.spawn_id, "Vurt", room)

        chief_mob.at_death()
        shaman_mob.at_death()

        # The tribe is frozen (repop.md §3).
        halted_until = (repop.db.halted_until or {}).get("hobgoblin")
        assert halted_until is not None and halted_until > time.time()

        # The designated rival (goblin) sends a scouting party (repop.md §4).
        scouts = repop.db.scouts or {}
        assert len(scouts) == repop_cfg.SCOUT_PARTY_SIZE
        assert all(s["faction"] == "goblin" for s in scouts.values())
        assert all(s["scouting"] == "hobgoblin" for s in scouts.values())

        # The halt applies the R2 leadership_broken tension spike with the rival.
        assert factions.get_tension("hobgoblin", "goblin") > baseline_tension
    finally:
        room.delete()


# ---------------------------------------------------------------------------
# Engine tests — faction standing shifts (faction.md §2.1 / M4↔zone tie)
# ---------------------------------------------------------------------------


def _teardown_room(room: Any, *characters: Any) -> None:
    """Delete room contents, the room, then any out-of-room characters."""
    for obj in list(room.contents):
        if obj.pk is not None:
            obj.delete()
    room.delete()
    for char in characters:
        if char.pk is not None:
            char.delete()


def _make_hobgoblin_mob(room: Any, key: str = "hobgoblin-grunt", *, is_leader: bool = False) -> Any:
    from evennia.utils import create  # noqa: PLC0415

    mob = create.create_object("typeclasses.npcs.Mob", key=key, location=room)
    mob.db.faction_id = "hobgoblin"
    mob.db.is_leader = is_leader
    return mob


@pytest.mark.django_db
def test_killing_hobgoblin_member_lowers_player_standing(
    repop_and_factions: tuple[Any, Any],
) -> None:
    """Slaying a rank-and-file hobgoblin drops the killer's hobgoblin standing."""
    _, factions = repop_and_factions
    from evennia.utils import create  # noqa: PLC0415

    room = create.create_object("typeclasses.rooms.Room", key="hobgoblin-standing-room-1")
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="hob-slayer-1")
    try:
        assert factions.get_standing("hobgoblin", str(char.id)) == 0
        mob = _make_hobgoblin_mob(room)
        mob.db.last_attacker = char
        mob.at_death()
        assert factions.get_standing("hobgoblin", str(char.id)) == STANDING_EVENTS["kill_member"]
    finally:
        _teardown_room(room, char)


@pytest.mark.django_db
def test_killing_hobgoblin_leader_lowers_standing_more(
    repop_and_factions: tuple[Any, Any],
) -> None:
    """A chief/shaman earns the larger kill_leader standing hit."""
    _, factions = repop_and_factions
    from evennia.utils import create  # noqa: PLC0415

    room = create.create_object("typeclasses.rooms.Room", key="hobgoblin-standing-room-2")
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="hob-slayer-2")
    try:
        king = _make_hobgoblin_mob(room, key="King-Nardo", is_leader=True)
        king.db.last_attacker = char
        king.at_death()
        assert factions.get_standing("hobgoblin", str(char.id)) == STANDING_EVENTS["kill_leader"]
    finally:
        _teardown_room(room, char)


@pytest.mark.django_db
def test_unattributed_hobgoblin_death_does_not_shift_standing(
    repop_and_factions: tuple[Any, Any],
) -> None:
    """A hobgoblin dying with no recorded attacker credits no one (faction.md §2.1)."""
    _, factions = repop_and_factions
    from evennia.utils import create  # noqa: PLC0415

    room = create.create_object("typeclasses.rooms.Room", key="hobgoblin-standing-room-3")
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="hobgoblin-bystander")
    try:
        mob = _make_hobgoblin_mob(room)  # last_attacker left None
        mob.at_death()
        assert factions.get_standing("hobgoblin", str(char.id)) == 0
    finally:
        _teardown_room(room, char)


@pytest.mark.django_db
def test_hobgoblin_kills_drive_standing_to_kos_and_survivor_aggros(
    repop_and_factions: tuple[Any, Any],
) -> None:
    """End-to-end M4↔zone tie: enough hobgoblin kills turn the tribe kill-on-sight."""
    _, factions = repop_and_factions
    from evennia.utils import create  # noqa: PLC0415

    room = create.create_object("typeclasses.rooms.Room", key="hobgoblin-kos-room")
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="hob-scourge")
    try:
        for i in range(10):
            mob = _make_hobgoblin_mob(room, key=f"hobgoblin-grunt-{i}")
            mob.db.last_attacker = char
            mob.at_death()
        assert factions.standing_band("hobgoblin", str(char.id)) == "kill-on-sight"

        _make_hobgoblin_mob(room, key="hobgoblin-sentry-survivor")
        messages: list[str] = []
        char.msg = lambda text, **_kw: messages.append(str(text))
        char.move_to(room, quiet=True)
        assert any("attacks" in m.lower() for m in messages)
    finally:
        _teardown_room(room, char)


# ---------------------------------------------------------------------------
# Group 6 — Tribe discovery (fanout-harness.md §3; pure, no Evennia)
# ---------------------------------------------------------------------------


def test_discovery_finds_hobgoblin_tribe() -> None:
    names = [m.__name__.rsplit(".", 1)[-1] for m in discovery.tribes()]
    assert "hobgoblin" in names
    found = [m for m in discovery.tribes() if m.__name__.rsplit(".", 1)[-1] == "hobgoblin"]
    assert found and callable(found[0].build)
