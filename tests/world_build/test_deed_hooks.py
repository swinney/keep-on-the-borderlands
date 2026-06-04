"""Tests for the world-event deed hooks (world-build §9, §13.8; M13 review F3).

M13 closed the deed-quest turn-in exploit by gating a deed-only quest's turn-in on
``QuestEntry.deed_done``, set only by ``world.quests.state.record_deed``. The world
events that *call* it were deferred to the world-build layer; ``world.build.events``
supplies them. Each hook finds a character's quest log and records the matching
deed.

Two layers:
  * Hook seam (``@pytest.mark.django_db`` for the ``character.db`` access): each hook
    sets ``deed_done`` for a character who has the deed quest accepted and is a
    no-op for one who does not — including the non-player / ``None`` cases.
  * Altar integration: the shrine-destroyed hook fires from ``Altar.at_destruction``
    and sets the flag **without** re-firing ``end_season`` (the altar stays the sole
    season-ender, review F4).
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest

from world.build import events
from world.quests import state as qstate
from world.quests.config import CATALOG

PLAYER_TYPECLASS = "typeclasses.characters.PlayerCharacter"
MOB_TYPECLASS = "typeclasses.npcs.Mob"
ALTAR_TYPECLASS = "typeclasses.objects.Altar"
ROOM_TYPECLASS = "typeclasses.rooms.Room"

# Each §9 hook paired with the deed quest it flips.
HOOKS: tuple[tuple[Any, str], ...] = (
    (events.shrine_destroyed, "c_destroy_shrine"),
    (events.rations_delivered, "p_supplies"),
    (events.captive_escorted, "c_rescue_soldier"),
    (events.spy_package_delivered, "sp_package"),
)


@pytest.fixture
def cleanup() -> Iterator[list[Any]]:
    """Track created objects and delete every one on teardown."""
    created: list[Any] = []
    try:
        yield created
    finally:
        for obj in created:
            if getattr(obj, "pk", None) is not None:
                obj.delete()


def _player(cleanup: list[Any], *, accepted: str | None = None) -> Any:
    """A player character, optionally with ``accepted`` quest active (deed pending)."""
    from evennia.utils import create  # noqa: PLC0415

    player = create.create_object(PLAYER_TYPECLASS, key="deed-seeker")
    cleanup.append(player)
    if accepted is not None:
        player.db.quests = {accepted: qstate.accept(CATALOG[accepted], None)}
    return player


def _deed_done(player: Any, quest_id: str) -> bool:
    return bool((player.db.quests or {}).get(quest_id, {}).get("deed_done", False))


# ── Hook seam: each deed hook flips the flag for a holder, no-ops otherwise ────


@pytest.mark.django_db
@pytest.mark.parametrize(("hook", "quest_id"), HOOKS)
def test_hook_sets_deed_for_holder(cleanup: list[Any], hook: Any, quest_id: str) -> None:
    """The world event sets ``deed_done`` for a character with the deed quest active."""
    player = _player(cleanup, accepted=quest_id)
    assert _deed_done(player, quest_id) is False

    assert hook(player) is True
    assert _deed_done(player, quest_id) is True


@pytest.mark.django_db
@pytest.mark.parametrize(("hook", "quest_id"), HOOKS)
def test_hook_noop_without_quest(cleanup: list[Any], hook: Any, quest_id: str) -> None:
    """The hook is a harmless no-op for a character who never accepted the quest."""
    player = _player(cleanup)  # empty quest log

    assert hook(player) is False
    assert player.db.quests in (None, {})


@pytest.mark.django_db
def test_hook_idempotent_second_fire_is_noop(cleanup: list[Any]) -> None:
    """Re-firing a deed event after the flag is set changes nothing (record_deed §)."""
    player = _player(cleanup, accepted="c_destroy_shrine")

    assert events.shrine_destroyed(player) is True
    assert events.shrine_destroyed(player) is False
    assert _deed_done(player, "c_destroy_shrine") is True


@pytest.mark.django_db
def test_credit_deed_noop_for_none_and_mob(cleanup: list[Any]) -> None:
    """``credit_deed`` ignores a missing character and a non-player mob."""
    from evennia.utils import create  # noqa: PLC0415

    assert events.credit_deed(None, "c_destroy_shrine") is False

    mob = create.create_object(MOB_TYPECLASS, key="bystander-mob")
    cleanup.append(mob)
    mob.db.quests = {"c_destroy_shrine": qstate.accept(CATALOG["c_destroy_shrine"], None)}
    assert events.credit_deed(mob, "c_destroy_shrine") is False
    assert _deed_done(mob, "c_destroy_shrine") is False


@pytest.mark.django_db
def test_hook_only_credits_active_quest(cleanup: list[Any]) -> None:
    """A completed (non-active) deed quest is not re-flagged by a later event."""
    player = _player(cleanup, accepted="p_supplies")
    log = dict(player.db.quests)
    log["p_supplies"]["state"] = qstate.COMPLETE
    player.db.quests = log

    assert events.rations_delivered(player) is False


# ── Altar integration: shrine-destroyed flag without re-firing end_season ─────


@pytest.fixture
def altar_room(cleanup: list[Any]) -> Any:
    """A room holding a fresh, intact Altar of Evil Chaos."""
    from evennia.utils import create  # noqa: PLC0415

    room = create.create_object(ROOM_TYPECLASS, key="altar room")
    cleanup.append(room)
    altar = create.create_object(ALTAR_TYPECLASS, key="altar", location=room)
    cleanup.append(altar)
    return altar


@pytest.fixture
def season() -> Iterator[Any]:
    """A live season_manager so the altar's end_season has a target."""
    from evennia.utils import create  # noqa: PLC0415

    manager = create.create_script("world.managers.season_manager.SeasonManager")
    try:
        yield manager
    finally:
        manager.delete()


@pytest.mark.django_db
def test_altar_destruction_sets_deed_without_refiring_end_season(
    cleanup: list[Any], altar_room: Any, season: Any
) -> None:
    """Shattering the altar flags the destroyer's deed and ends the season exactly once.

    The destroyer is recorded as the altar's ``last_attacker`` (the same seam a mob
    uses); ``at_destruction`` both ends the season (its sole R6 trigger) and sets
    the ``c_destroy_shrine`` deed flag — the deed hook does not add a second
    ``end_season``, so the counter advances by exactly one.
    """
    altar = altar_room
    destroyer = _player(cleanup, accepted="c_destroy_shrine")
    altar.db.last_attacker = destroyer
    closing_season = season.db.season_number

    altar.apply_damage(int(altar.db.hp) + 50)  # an overkill killing blow

    assert altar.db.destroyed is True
    assert _deed_done(destroyer, "c_destroy_shrine") is True
    # End_season fired once (the altar's), not twice (the deed hook adds none).
    assert season.db.season_number == closing_season + 1


@pytest.mark.django_db
def test_altar_destruction_without_destroyer_only_ends_season(
    cleanup: list[Any], altar_room: Any, season: Any
) -> None:
    """With no recorded attacker the altar still ends the season; the deed is a no-op."""
    altar = altar_room
    closing_season = season.db.season_number

    altar.apply_damage(int(altar.db.hp) + 50)

    assert altar.db.destroyed is True
    assert season.db.season_number == closing_season + 1


@pytest.mark.django_db
def test_shrine_hook_alone_does_not_need_season_manager(cleanup: list[Any]) -> None:
    """The hook itself only touches the quest log — it never reaches end_season.

    No season_manager exists in this test; calling the hook directly still flags the
    deed and raises nothing, proving the season-end is the altar's job, not the hook's.
    """
    player = _player(cleanup, accepted="c_destroy_shrine")

    assert events.shrine_destroyed(player) is True
    assert _deed_done(player, "c_destroy_shrine") is True
