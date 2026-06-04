"""Tests for quest-giver resolution by explicit giver-key (world-build §8, §13.7).

M13 review F1: ``commands.quests._giver_here`` used to match an NPC by its
display ``db.role``, so only the Guildmaster and Castellan (whose role happens to
equal their giver-key) resolved — the Hermit, Provisioner, the spy, and the
tribe-chief givers were unreachable. The fix gives every giver an explicit
``db.giver_key`` (from ``world.quests.config.GIVERS``) that the builder and the
spawner write through, and resolves on that.

Two layers:
  * Pure (Django-free): the static zone data carries ``giver_key`` for each giver.
  * Engine (``@pytest.mark.django_db``): the builder/spawner write-through and
    ``_giver_here`` resolution, including the chief alive-and-present rule.
"""

from __future__ import annotations

import random
from collections.abc import Iterator
from typing import Any

import pytest

from commands.quests import _giver_here
from world.build import spawner, templates
from world.quests.config import GIVERS
from world.repop.state import SpawnPoint
from world.zones.builder import ROOM_CATEGORY, build_npcs, build_rooms, find_npc
from world.zones.keep import npcs as keep_npcs
from world.zones.records import NpcRecord, RoomRecord
from world.zones.wilderness import npcs as wild_npcs

MOB_TYPECLASS = "typeclasses.npcs.Mob"
SERVICE_TYPECLASS = "typeclasses.npcs.ServiceNpc"
ROOM_TYPECLASS = "typeclasses.rooms.Room"
PLAYER_TYPECLASS = "typeclasses.characters.PlayerCharacter"

# A quest-giving chief template (orc_vs_orc rivalry); carries giver_key after the
# slice-4 wiring, so the spawner writes it onto the live mob.
CHIEF_KEY = "orc_vol_chief"


# ── Pure: the static zone data carries giver_key for each giver ──────────────


def test_keep_givers_carry_giver_key() -> None:
    """The Guildmaster, Castellan, and Curate records name their giver-key."""
    by_key = {record["key"]: record for record in keep_npcs.NPCS}
    for npc_key in ("guildmaster", "castellan", "curate"):
        giver_key = by_key[npc_key].get("giver_key")
        assert giver_key == npc_key
        assert giver_key in GIVERS


def test_hermit_carries_giver_key_despite_display_role() -> None:
    """The Hermit's display role is 'encounter', but its giver-key is set (F1)."""
    hermit = next(r for r in wild_npcs.NPCS if r["key"] == "mad_hermit")
    assert hermit["role"] == "encounter"
    assert hermit.get("giver_key") == "mad_hermit"
    assert "mad_hermit" in GIVERS


def test_chief_templates_carry_giver_key() -> None:
    """The quest-giving chiefs name their giver-key on the mob template."""
    registry = templates.all_templates()
    for chief in ("orc_vol_chief", "orc_dec_chief", "goblin_chief"):
        giver_key = registry[chief].get("giver_key")
        assert giver_key == chief
        assert giver_key in GIVERS


# ── Engine fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def room_factory() -> Iterator[Any]:
    """Build tagged rooms on demand and tear every one (plus its contents) down."""
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


def _service_npc(room: Any, *, giver_key: str | None, role: str) -> Any:
    from evennia.utils import create  # noqa: PLC0415

    npc = create.create_object(SERVICE_TYPECLASS, key=f"npc-{role}", location=room)
    npc.db.role = role
    npc.db.giver_key = giver_key
    return npc


def _player(room: Any) -> Any:
    from evennia.utils import create  # noqa: PLC0415

    return create.create_object(PLAYER_TYPECLASS, key="seeker", location=room)


# ── Engine: _giver_here resolves on giver_key ────────────────────────────────


@pytest.mark.django_db
def test_servicenpc_giver_resolves_regardless_of_role(room_factory: Any) -> None:
    """An NPC giver whose display role differs from its key is still reachable (F1)."""
    room = room_factory("zone:hut")
    # The Provisioner-style case: a giver-key that no display role matches.
    _service_npc(room, giver_key="provisioner", role="shopkeeper")
    caller = _player(room)

    assert _giver_here(caller) == "provisioner"


@pytest.mark.django_db
def test_mob_chief_giver_resolves(room_factory: Any) -> None:
    """A plain Mob chief carrying a giver-key resolves (not just ServiceNpcs)."""
    from evennia.utils import create  # noqa: PLC0415

    room = room_factory("zone:lair")
    chief = create.create_object(MOB_TYPECLASS, key="Grukk", location=room)
    chief.db.giver_key = "orc_vol_chief"
    caller = _player(room)

    assert _giver_here(caller) == "orc_vol_chief"


@pytest.mark.django_db
def test_non_giver_npc_is_not_resolved(room_factory: Any) -> None:
    """An NPC with only a display role and no giver-key offers no quests."""
    room = room_factory("zone:tavern")
    _service_npc(room, giver_key=None, role="tavernkeeper")
    caller = _player(room)

    assert _giver_here(caller) is None


@pytest.mark.django_db
def test_no_giver_present_is_none(room_factory: Any) -> None:
    """An empty room (just the caller) resolves to no giver."""
    room = room_factory("zone:empty")
    caller = _player(room)

    assert _giver_here(caller) is None


# ── Engine: builder & spawner write-through ──────────────────────────────────


@pytest.mark.django_db
def test_builder_writes_giver_key(room_factory: Any) -> None:
    """build_npcs writes record['giver_key'] onto the live NPC (world-build §8)."""
    room_factory("zone:hall")
    rooms: list[RoomRecord] = [{"key": "hall", "name": "A Hall", "desc": "stone.", "zone": "zone"}]
    given: NpcRecord = {
        "key": "patron",
        "name": "The Patron",
        "sdesc": "a patron",
        "role": "noble",
        "giver_key": "castellan",
    }
    plain: NpcRecord = {
        "key": "barkeep",
        "name": "A Barkeep",
        "sdesc": "a barkeep",
        "role": "tavernkeeper",
    }
    build_rooms("zone", rooms)
    build_npcs("zone", [given, plain], {"patron": "hall", "barkeep": "hall"})

    assert find_npc("zone", "patron").db.giver_key == "castellan"
    # An NPC record with no giver_key leaves the attribute cleared (idempotent).
    assert find_npc("zone", "barkeep").db.giver_key is None


@pytest.mark.django_db
def test_spawner_writes_giver_key(room_factory: Any) -> None:
    """spawn_mob writes the template's giver_key onto a quest-giving chief (§8)."""
    room_factory("caves:orc_vol_chief")
    point = SpawnPoint(
        spawn_id="caves:orc_vol_chief:orc_vol_chief:0",
        room="caves:orc_vol_chief",
        mob_template=CHIEF_KEY,
        faction="orc_vol",
        is_leader=True,
        leader_role="chief",
    )

    mob = spawner.spawn_mob(point, rng=random.Random(1))

    assert mob is not None
    assert mob.db.giver_key == "orc_vol_chief"


# ── Engine: chief alive-and-present rule (§8) ────────────────────────────────


@pytest.mark.django_db
def test_chief_giver_unavailable_while_dead_then_back_after_respawn(room_factory: Any) -> None:
    """A live chief is a reachable giver; a slain one is not, until it respawns (§8)."""
    room = room_factory("caves:orc_vol_chief")
    point = SpawnPoint(
        spawn_id="caves:orc_vol_chief:orc_vol_chief:0",
        room="caves:orc_vol_chief",
        mob_template=CHIEF_KEY,
        faction="orc_vol",
        is_leader=True,
        leader_role="chief",
    )
    chief = spawner.spawn_mob(point, rng=random.Random(1))
    caller = _player(room)

    # Alive and present: the chief gives quests.
    assert _giver_here(caller) == "orc_vol_chief"

    # Slain: its corpse lingers in the lair but offers no quests.
    chief.traits.hp.current = 0
    assert spawner._is_dead(chief)
    assert _giver_here(caller) is None

    # Respawn (the repop path clears the corpse and re-creates a live chief).
    fresh = spawner.spawn_mob(point, rng=random.Random(2))
    assert fresh.id != chief.id
    assert _giver_here(caller) == "orc_vol_chief"
