"""Build-time engine tests for the Keep (zones spec §6: 1, 2, 6, 7).

Boots Evennia (pytest-django) to verify that build() materialises the rooms and
exits, marks the Inner Bailey as the recall point, and is idempotent.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from evennia.utils.search import search_object_by_tag

from world.zones import keep
from world.zones.builder import EXIT_CATEGORY, RECALL_TAG, ROOM_CATEGORY


def _keep_rooms() -> list[Any]:
    return list(search_object_by_tag(category=ROOM_CATEGORY))


def _keep_exits() -> list[Any]:
    return list(search_object_by_tag(category=EXIT_CATEGORY))


def _find_room(room_key: str) -> Any:
    matches = search_object_by_tag(f"keep:{room_key}", category=ROOM_CATEGORY)
    return matches[0] if matches else None


@pytest.fixture
def built_keep() -> Iterator[None]:
    """Build the Keep, yield, then tear down every room/exit it created."""
    keep.build()
    try:
        yield
    finally:
        for exit_ in _keep_exits():
            exit_.delete()
        for room in _keep_rooms():
            room.delete()


@pytest.mark.django_db
def test_build_creates_every_room(built_keep: None) -> None:
    built_keys = {r.db.room_key for r in _keep_rooms()}
    assert built_keys == {r["key"] for r in keep.ROOMS}


@pytest.mark.django_db
def test_build_tags_inner_bailey_as_recall(built_keep: None) -> None:
    recall_rooms = search_object_by_tag(RECALL_TAG)
    assert len(recall_rooms) == 1
    assert recall_rooms[0].db.room_key == "inner_bailey"


@pytest.mark.django_db
def test_build_wires_a_reversible_exit(built_keep: None) -> None:
    inner_gate = _find_room("inner_gate")
    inner_bailey = _find_room("inner_bailey")
    north = [e for e in inner_gate.exits if e.key == "n"]
    assert north and north[0].destination == inner_bailey
    south = [e for e in inner_bailey.exits if e.key == "s"]
    assert south and south[0].destination == inner_gate


@pytest.mark.django_db
def test_main_gate_wilderness_exit_skipped_until_wilderness_exists(built_keep: None) -> None:
    # The wilderness target room does not exist yet, so its exit is not wired.
    main_gate = _find_room("main_gate")
    assert [e for e in main_gate.exits if e.key == "s"] == []


@pytest.mark.django_db
def test_build_is_idempotent(built_keep: None) -> None:
    first_rooms = {r.id for r in _keep_rooms()}
    first_exits = {e.id for e in _keep_exits()}
    keep.build()
    assert {r.id for r in _keep_rooms()} == first_rooms
    assert {e.id for e in _keep_exits()} == first_exits
