"""Tests for the live mob spawner (world-build spec §6-§7, §13.2-§13.3, §13.6).

Two layers:
  * Pure (Django-free): the HD→dice translation, the seeded HP roll, and the
    rival-scout template pick — they import the spawner but never touch Evennia.
  * Engine (``@pytest.mark.django_db``): ``spawn_mob`` / ``spawn_scout`` /
    ``despawn`` materialising records into live ``Mob`` objects, plus the
    ``repop_manager`` delegation that replaces its old no-ops.
"""

from __future__ import annotations

import random
from collections.abc import Iterator
from typing import Any

import pytest

from world.build import spawner, templates
from world.repop.state import Scout, SpawnPoint
from world.zones.builder import ROOM_CATEGORY

MOB_TYPECLASS = "typeclasses.npcs.Mob"
ROOM_TYPECLASS = "typeclasses.rooms.Room"

# The kobold chief: a leader template (ac 13, level 2, morale 8) whose HP rolls
# from "1+1" → 1d8+1. Used across the materialisation tests.
CHIEF_ROOM = "caves:kobold_den"
CHIEF_KEY = "kobold_chief"


def _chief_point(room: str = CHIEF_ROOM) -> SpawnPoint:
    return SpawnPoint(
        spawn_id="caves:kobold_den:kobold_chief:0",
        room=room,
        mob_template=CHIEF_KEY,
        faction="kobold",
        is_leader=True,
        leader_role="chief",
    )


# ── Pure helpers ─────────────────────────────────────────────────────────────


def test_hd_notation_count_is_d8() -> None:
    """A bare OSE HD count (optionally +/- a flat hp modifier) maps onto d8s."""
    assert spawner.hd_notation("2") == "2d8"
    assert spawner.hd_notation("1+1") == "1d8+1"
    assert spawner.hd_notation("1-1") == "1d8-1"
    assert spawner.hd_notation("3+1") == "3d8+1"


def test_hd_notation_explicit_die_passthrough() -> None:
    """An explicit die (sub-HD monsters like the 1d4 kobold) passes through."""
    assert spawner.hd_notation("1d4") == "1d4"
    assert spawner.hd_notation(" 1d8 ") == "1d8"


def test_hd_notation_malformed_raises() -> None:
    with pytest.raises(ValueError, match="malformed hit dice"):
        spawner.hd_notation("ogre")


def test_roll_hp_is_deterministic_under_seed() -> None:
    """The same record + same seed yields the same HP (the §13.2 RNG seam)."""
    record = {
        "key": "k",
        "name": "K",
        "faction": "kobold",
        "level": 2,
        "hd": "2",
        "ac": 12,
        "attacks": "1d6",
        "morale": 8,
    }
    first = spawner.roll_hp(record, random.Random(7))  # type: ignore[arg-type]
    second = spawner.roll_hp(record, random.Random(7))  # type: ignore[arg-type]
    assert first == second
    assert first >= 1


def test_roll_hp_floors_at_one() -> None:
    """A "1-1" mob whose dice roll 1 still spawns at 1 HP, never 0."""
    record = {
        "key": "k",
        "name": "K",
        "faction": "kobold",
        "level": 1,
        "hd": "1-1",
        "ac": 12,
        "attacks": "1d4",
        "morale": 6,
    }
    # Seed search: every 1d8-1 outcome is floored at 1, so any seed yields >= 1.
    assert all(spawner.roll_hp(record, random.Random(s)) >= 1 for s in range(20))  # type: ignore[arg-type]


def test_scout_template_picks_nonleader_of_faction() -> None:
    """A scout's faction resolves to a rank-and-file (non-leader) template."""
    record = spawner._scout_template("orc_vol")
    assert record is not None
    assert record["faction"] == "orc_vol"
    assert not record.get("is_leader")


def test_scout_template_unknown_faction_is_none() -> None:
    assert spawner._scout_template("no_such_faction") is None


# ── Engine materialisation ───────────────────────────────────────────────────


@pytest.fixture
def room_factory() -> Iterator[Any]:
    """Build tagged rooms on demand and tear every one (plus its mobs) down."""
    from evennia.utils import create  # noqa: PLC0415

    built: list[Any] = []

    def make(identity: str) -> Any:
        room = create.create_object(ROOM_TYPECLASS, key=identity)
        room.tags.add(identity, category=ROOM_CATEGORY)
        built.append(room)
        return room

    try:
        yield make
    finally:
        for room in built:
            for obj in list(room.contents):
                if obj.pk is not None:
                    obj.delete()
            if room.pk is not None:
                room.delete()


@pytest.mark.django_db
def test_spawn_mob_materializes_record(room_factory: Any) -> None:
    """spawn_mob wires ac/hp/level/morale/faction/is_leader/spawn_id from the record."""
    room = room_factory(CHIEF_ROOM)
    point = _chief_point()
    expected_hp = spawner.roll_hp(templates.get_template(CHIEF_KEY), random.Random(99))

    mob = spawner.spawn_mob(point, rng=random.Random(99))

    assert mob is not None
    assert mob.location == room
    assert int(mob.traits.ac.value) == 13
    assert int(mob.traits.level.value) == 2
    assert int(mob.traits.morale.value) == 8
    assert int(mob.traits.hp.value) == expected_hp
    assert mob.db.faction_id == "kobold"
    assert mob.db.is_leader is True
    assert mob.db.spawn_id == point.spawn_id
    assert mob.tags.has(point.spawn_id, category=spawner.SPAWN_INSTANCE_CATEGORY)


@pytest.mark.django_db
def test_spawn_mob_returns_none_when_room_unbuilt() -> None:
    """The deferred-room safety property: no room → None, no mob, no raise (§13.3)."""
    point = _chief_point(room="caves:not_built")
    assert spawner.spawn_mob(point, rng=random.Random(1)) is None


@pytest.mark.django_db
def test_spawn_mob_is_idempotent(room_factory: Any) -> None:
    """A second spawn of a live point returns the same mob — exactly one instance (§7)."""
    from evennia.utils.search import search_object_by_tag  # noqa: PLC0415

    room_factory(CHIEF_ROOM)
    point = _chief_point()

    first = spawner.spawn_mob(point, rng=random.Random(1))
    second = spawner.spawn_mob(point, rng=random.Random(1))

    assert second.id == first.id
    instances = search_object_by_tag(point.spawn_id, category=spawner.SPAWN_INSTANCE_CATEGORY)
    assert len(instances) == 1


@pytest.mark.django_db
def test_spawn_mob_respawns_after_death(room_factory: Any) -> None:
    """A dead instance is cleared and re-created — the respawn path (§13.6)."""
    from evennia.utils.search import search_object_by_tag  # noqa: PLC0415

    room_factory(CHIEF_ROOM)
    point = _chief_point()

    dead = spawner.spawn_mob(point, rng=random.Random(1))
    dead.traits.hp.current = 0  # killed
    assert spawner._is_dead(dead)

    fresh = spawner.spawn_mob(point, rng=random.Random(1))

    assert fresh.id != dead.id
    assert dead.pk is None  # the corpse instance was cleared
    instances = search_object_by_tag(point.spawn_id, category=spawner.SPAWN_INSTANCE_CATEGORY)
    assert len(instances) == 1
    assert not spawner._is_dead(fresh)


@pytest.mark.django_db
def test_spawn_scout_materializes_rival(room_factory: Any) -> None:
    """A scout instance carries the rival faction + scout_id, not a spawn_id (§6)."""
    room = room_factory(CHIEF_ROOM)
    scout = Scout(
        scout_id="orc_vol_scout_kobold_0", faction="orc_vol", room=CHIEF_ROOM, scouting="kobold"
    )

    mob = spawner.spawn_scout(scout, rng=random.Random(3))

    assert mob is not None
    assert mob.location == room
    assert mob.db.faction_id == "orc_vol"
    assert mob.db.is_leader is False
    assert mob.db.scout_id == scout.scout_id
    assert mob.db.spawn_id is None
    assert mob.tags.has(scout.scout_id, category=spawner.SPAWN_INSTANCE_CATEGORY)


@pytest.mark.django_db
def test_despawn_removes_instance(room_factory: Any) -> None:
    """despawn deletes the tagged instance and reports whether one existed (§13.6)."""
    from evennia.utils.search import search_object_by_tag  # noqa: PLC0415

    room_factory(CHIEF_ROOM)
    scout = Scout(
        scout_id="orc_vol_scout_kobold_0", faction="orc_vol", room=CHIEF_ROOM, scouting="kobold"
    )
    mob = spawner.spawn_scout(scout, rng=random.Random(3))

    assert spawner.despawn(scout.scout_id) is True
    assert mob.pk is None
    assert not search_object_by_tag(scout.scout_id, category=spawner.SPAWN_INSTANCE_CATEGORY)
    # A second despawn (nothing left) reports False.
    assert spawner.despawn(scout.scout_id) is False


# ── repop_manager delegation (the rewired no-ops) ────────────────────────────


@pytest.fixture
def repop_manager() -> Iterator[Any]:
    from evennia.utils import create  # noqa: PLC0415

    manager = create.create_script("world.managers.repop_manager.RepopManager")
    try:
        yield manager
    finally:
        manager.delete()


@pytest.mark.django_db
def test_manager_instantiate_delegates_to_spawner(room_factory: Any, repop_manager: Any) -> None:
    """repop_manager._instantiate now materialises a live mob (no longer a no-op)."""
    room = room_factory(CHIEF_ROOM)
    point = _chief_point()

    repop_manager._instantiate(point)

    mobs = [o for o in room.contents if getattr(o, "IS_MOB", False)]
    assert len(mobs) == 1
    assert mobs[0].db.spawn_id == point.spawn_id


@pytest.mark.django_db
def test_manager_retreat_scout_delegates_to_despawn(room_factory: Any, repop_manager: Any) -> None:
    """repop_manager._retreat_scout despawns the live scout instance (§4)."""
    room = room_factory(CHIEF_ROOM)
    scout = Scout(
        scout_id="orc_vol_scout_kobold_0", faction="orc_vol", room=CHIEF_ROOM, scouting="kobold"
    )
    spawner.spawn_scout(scout, rng=random.Random(3))

    repop_manager._retreat_scout(scout)

    assert not [o for o in room.contents if getattr(o, "IS_MOB", False)]


@pytest.mark.django_db
def test_scout_death_notifies_manager(room_factory: Any, repop_manager: Any) -> None:
    """A killed scout reports via notify_scout_death — not the respawn path (§4).

    The spawner tags the instance with ``scout_id`` (no ``spawn_id``); ``Mob.at_death``
    must route a scout kill to ``notify_scout_death`` so scouting state updates (a
    scout does not respawn), closing the M15 F3 wiring gap.
    """
    from dataclasses import asdict  # noqa: PLC0415

    from evennia.utils import create  # noqa: PLC0415

    room = room_factory(CHIEF_ROOM)
    scout = Scout(
        scout_id="orc_vol_scout_kobold_0", faction="orc_vol", room=CHIEF_ROOM, scouting="kobold"
    )
    # Seed the manager's scouting state so notify_scout_death can resolve + clear it.
    repop_manager.db.scouts = {scout.scout_id: asdict(scout)}
    mob = spawner.spawn_scout(scout, rng=random.Random(3))
    assert mob.location == room
    assert mob.db.scout_id == scout.scout_id and mob.db.spawn_id is None
    killer = create.create_object("typeclasses.characters.PlayerCharacter", key="raider")
    mob.db.last_attacker = killer
    try:
        mob.at_death()

        # notify_scout_death fired: the scout is cleared from scouting state and
        # does not respawn (the spawn-point notify_death path was never taken).
        assert scout.scout_id not in (repop_manager.db.scouts or {})
    finally:
        killer.delete()
