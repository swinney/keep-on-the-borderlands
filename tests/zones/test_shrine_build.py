"""Build-time + reset engine tests for the Shrine (zones spec §Systems wiring).

Boots Evennia (pytest-django) to verify that build() materialises the temple
rooms with their dark/no_recall flags and reversible exits, that the inter-zone
link to the Caves is deferred until the Caves exist, and that the 24h Shrine
reset restocks the cult wholesale through the repop_manager (M11 §5).
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from typing import Any

import pytest
from evennia.utils.search import search_object_by_tag

from world.zones import shrine
from world.zones.builder import EXIT_CATEGORY, FLAG_CATEGORY, ROOM_CATEGORY
from world.zones.spawn_registry import spawn_points


def _shrine_rooms() -> list[Any]:
    return list(search_object_by_tag(category=ROOM_CATEGORY))


def _shrine_exits() -> list[Any]:
    return list(search_object_by_tag(category=EXIT_CATEGORY))


def _find_room(room_key: str) -> Any:
    matches = search_object_by_tag(f"shrine:{room_key}", category=ROOM_CATEGORY)
    return matches[0] if matches else None


@pytest.fixture
def built_shrine() -> Iterator[None]:
    """Build the Shrine, yield, then tear down every room/exit it created."""
    shrine.build()
    try:
        yield
    finally:
        for exit_ in _shrine_exits():
            exit_.delete()
        for room in _shrine_rooms():
            room.delete()


@pytest.mark.django_db
def test_build_creates_every_room(built_shrine: None) -> None:
    built_keys = {r.db.room_key for r in _shrine_rooms()}
    assert built_keys == {r["key"] for r in shrine.ROOMS}


@pytest.mark.django_db
def test_build_applies_dark_and_no_recall_flags(built_shrine: None) -> None:
    expected_dark = {r["key"] for r in shrine.ROOMS if r.get("dark")}
    expected_no_recall = {r["key"] for r in shrine.ROOMS if r.get("no_recall")}
    dark = {r.db.room_key for r in _shrine_rooms() if r.tags.has("dark", category=FLAG_CATEGORY)}
    no_recall = {
        r.db.room_key for r in _shrine_rooms() if r.tags.has("no_recall", category=FLAG_CATEGORY)
    }
    assert dark == expected_dark
    assert no_recall == expected_no_recall


@pytest.mark.django_db
def test_build_wires_a_reversible_exit(built_shrine: None) -> None:
    narthex = _find_room("narthex")
    nave = _find_room("nave_evil")
    north = [e for e in narthex.exits if e.key == "n"]
    assert north and north[0].destination == nave
    south = [e for e in nave.exits if e.key == "s"]
    assert south and south[0].destination == narthex


@pytest.mark.django_db
def test_minotaur_link_skipped_until_caves_exists(built_shrine: None) -> None:
    # The Caves minotaur room is not built here, so the up exit is not wired.
    gate = _find_room("shrine_gate")
    assert [e for e in gate.exits if e.key == "u"] == []


@pytest.mark.django_db
def test_build_is_idempotent(built_shrine: None) -> None:
    first_rooms = {r.id for r in _shrine_rooms()}
    first_exits = {e.id for e in _shrine_exits()}
    shrine.build()
    assert {r.id for r in _shrine_rooms()} == first_rooms
    assert {e.id for e in _shrine_exits()} == first_exits


# ── 24h reset: the cult restocks wholesale through the repop_manager (§5) ─────


@pytest.fixture
def repop_manager() -> Iterator[Any]:
    """A repop_manager with the Shrine zone registered, torn down after the test."""
    from evennia.utils import create  # noqa: PLC0415

    repop = create.create_script("world.managers.repop_manager.RepopManager")
    repop.register_zone(shrine.ZONE, shrine.SPAWNS, shrine.MOB_TEMPLATES)
    try:
        yield repop
    finally:
        repop.delete()


def _a_cult_spawn_id() -> str:
    """The Adept's spawn id, derived the same way the manager registers it."""
    points = spawn_points(shrine.ZONE, shrine.SPAWNS, shrine.MOB_TEMPLATES)
    return next(p.spawn_id for p in points if p.mob_template == "the_adept")


@pytest.mark.django_db
def test_24h_reset_restocks_dead_cult_mobs(repop_manager: Any) -> None:
    """A slain cult mob is brought back when the 24h Shrine reset fires (§5)."""
    repop = repop_manager
    spawn_id = _a_cult_spawn_id()

    # The Adept is slain — its respawn is pending on the 24h cadence.
    repop.notify_death(spawn_id)
    assert spawn_id in (repop.db.respawn_at or {})

    # First tick arms the Shrine's 24h cycle (nothing is due yet).
    repop.at_repeat()
    assert repop.db.shrine_reset_at is not None
    assert spawn_id in (repop.db.respawn_at or {})

    # Force the 24h boundary into the past, then tick: the reset restocks the
    # whole cult, so the Adept is alive again (no pending respawn).
    repop.db.shrine_reset_at = time.time() - 1
    repop.at_repeat()
    assert spawn_id not in (repop.db.respawn_at or {})
    # And the cycle re-arms for the next 24h window.
    assert repop.db.shrine_reset_at > time.time()
