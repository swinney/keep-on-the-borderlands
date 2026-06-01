"""Keep NPC integration: tavern roster host + chapel staff (priest pool).

Pure-data tests validate the NPC records and placement without booting Evennia;
the build-time tests (pytest-django) verify that build() materialises each NPC
in its room, tags the disguised-priest pool, and stays idempotent.

Spec: docs/specs/zones/keep.md (NPC table), docs/specs/disguised-priest.md §2
(the five-NPC pool), docs/specs/henchmen.md §1 (tavern roster).
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from evennia.utils.search import search_object_by_tag

from world.zones import keep
from world.zones.builder import (
    EXIT_CATEGORY,
    NPC_CATEGORY,
    PRIEST_POOL_TAG,
    ROOM_CATEGORY,
    find_npc,
)
from world.zones.keep import npcs as keep_npcs

EXPECTED_POOL = {"anselm", "maeve", "ortho", "bellan", "gisla"}

# sdescs straight from disguised-priest.md §2 — the pool's observable identities.
EXPECTED_POOL_SDESCS = {
    "anselm": "a soft-spoken friar",
    "maeve": "a stern sister",
    "ortho": "a portly deacon",
    "bellan": "a young bellringer",
    "gisla": "a wandering pardoner",
}


# ── pure-data validation ────────────────────────────────────────────────────


def test_npcs_are_well_formed() -> None:
    """Every NPC record carries a non-empty key, name, sdesc, and role."""
    assert keep.NPCS, "the Keep now ships static NPCs"
    for record in keep.NPCS:
        assert record["key"].strip()
        assert record["name"].strip()
        assert record["sdesc"].strip()
        assert record["role"].strip()


def test_npc_keys_unique() -> None:
    """No two NPC records share a key."""
    keys = [r["key"] for r in keep.NPCS]
    assert len(keys) == len(set(keys))


def test_every_npc_is_placed_in_a_real_room() -> None:
    """PLACEMENT covers every NPC and names only real Keep rooms."""
    room_keys = {r["key"] for r in keep.ROOMS}
    npc_keys = {r["key"] for r in keep.NPCS}
    assert set(keep_npcs.PLACEMENT) == npc_keys
    for room_key in keep_npcs.PLACEMENT.values():
        assert room_key in room_keys


def test_tavernkeeper_anchors_the_roster() -> None:
    """A tavernkeeper NPC stands in the tavern (the henchmen hiring hall)."""
    by_key = {r["key"]: r for r in keep.NPCS}
    assert "tavernkeeper" in by_key
    assert by_key["tavernkeeper"]["role"] == "tavernkeeper"
    assert keep_npcs.PLACEMENT["tavernkeeper"] == "tavern"


def test_curate_in_chapel_nave() -> None:
    """The Curate (dialogue-detection NPC, R4) stands in the chapel nave."""
    by_key = {r["key"]: r for r in keep.NPCS}
    assert "curate" in by_key
    assert keep_npcs.PLACEMENT["curate"] == "chapel_nave"


def test_priest_pool_is_the_five_chapel_staff() -> None:
    """The pool is exactly the five disguised-priest candidates with spec sdescs."""
    assert set(keep_npcs.PRIEST_POOL) == EXPECTED_POOL
    by_key = {r["key"]: r for r in keep.NPCS}
    for key, sdesc in EXPECTED_POOL_SDESCS.items():
        assert key in by_key
        assert by_key[key]["sdesc"] == sdesc


def test_pool_npcs_live_in_chapel_rooms() -> None:
    """Every pool NPC is placed in a chapel room (nave/vestry/bell tower)."""
    chapel_rooms = {"chapel_nave", "chapel_vestry", "chapel_bell"}
    for key in keep_npcs.PRIEST_POOL:
        assert keep_npcs.PLACEMENT[key] in chapel_rooms


# ── build-time engine behaviour ─────────────────────────────────────────────


def _keep_rooms() -> list[Any]:
    return list(search_object_by_tag(category=ROOM_CATEGORY))


def _keep_npcs() -> list[Any]:
    return list(search_object_by_tag(category=NPC_CATEGORY))


@pytest.fixture
def built_keep() -> Iterator[None]:
    """Build the Keep, yield, then tear down every NPC/room it created."""
    keep.build()
    try:
        yield
    finally:
        for npc in _keep_npcs():
            npc.delete()
        for exit_ in search_object_by_tag(category=EXIT_CATEGORY):
            exit_.delete()
        for room in _keep_rooms():
            room.delete()


@pytest.mark.django_db
def test_build_places_every_npc_in_its_room(built_keep: None) -> None:
    built_keys = {npc.db.npc_key for npc in _keep_npcs()}
    assert built_keys == {r["key"] for r in keep.NPCS}
    for record in keep.NPCS:
        npc = find_npc("keep", record["key"])
        assert npc is not None
        assert npc.location.db.room_key == keep_npcs.PLACEMENT[record["key"]]
        assert npc.db.sdesc == record["sdesc"]
        assert npc.db.role == record["role"]


@pytest.mark.django_db
def test_build_tags_the_priest_pool(built_keep: None) -> None:
    pool = search_object_by_tag(PRIEST_POOL_TAG)
    assert {npc.db.npc_key for npc in pool} == EXPECTED_POOL


@pytest.mark.django_db
def test_tavernkeeper_is_peaceful(built_keep: None) -> None:
    """The placed tavernkeeper is a ServiceNpc with no aggressive faction."""
    keeper = find_npc("keep", "tavernkeeper")
    assert getattr(keeper, "IS_SERVICE_NPC", False)
    assert keeper.db.faction_id is None


@pytest.mark.django_db
def test_build_npcs_is_idempotent(built_keep: None) -> None:
    first = {npc.id for npc in _keep_npcs()}
    keep.build()
    assert {npc.id for npc in _keep_npcs()} == first
