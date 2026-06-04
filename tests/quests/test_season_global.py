"""Engine tests for the two season-global quest effects (docs/specs/quests.md §8, §9.8-§9.9).

Boots Django/Evennia (pytest-django) to verify the live wiring the pure tests
can't: the Castellan stands in his audience chamber, and turning in his two story
quests fires the server-wide events through their global-Script managers —
``c_expose_priest`` trips the disguised-priest exposure (R4) when reported with
valid evidence, and ``c_destroy_shrine`` ends the season early (R6) and pays its
reward. Mirrors the M9 Guildmaster engine harness in
``test_guildmaster_engine.py``.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from evennia.utils import create
from evennia.utils.search import search_object_by_tag

from commands.quests import CmdAccept, CmdTurnin
from world.priest import config as priest_cfg
from world.quests import state as qstate
from world.zones import keep
from world.zones.builder import EXIT_CATEGORY, NPC_CATEGORY, ROOM_CATEGORY, find_npc

EXPOSE_PRIEST = "c_expose_priest"
DESTROY_SHRINE = "c_destroy_shrine"


def _keep_rooms() -> list[Any]:
    return list(search_object_by_tag(category=ROOM_CATEGORY))


@pytest.fixture
def keep_with_managers() -> Iterator[tuple[Any, Any]]:
    """Build the Keep and register the priest + season managers; tear all down."""
    keep.build()
    factions = create.create_script("world.managers.faction_manager.FactionManager")
    priest = create.create_script("world.managers.priest_manager.PriestManager")
    season = create.create_script("world.managers.season_manager.SeasonManager")
    try:
        yield priest, season
    finally:
        for script in (factions, priest, season):
            script.delete()
        for npc in search_object_by_tag(category=NPC_CATEGORY):
            npc.delete()
        for exit_ in search_object_by_tag(category=EXIT_CATEGORY):
            exit_.delete()
        for room in _keep_rooms():
            room.delete()


def _audience_room() -> Any:
    matches = search_object_by_tag("keep:audience", category=ROOM_CATEGORY)
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


@pytest.mark.django_db
def test_castellan_stands_in_the_audience_chamber(keep_with_managers: Any) -> None:
    castellan = find_npc("keep", "castellan")
    assert castellan is not None
    assert castellan.location.db.room_key == "audience"
    assert getattr(castellan, "IS_SERVICE_NPC", False)
    assert castellan.db.role == "castellan"


@pytest.mark.django_db
def test_expose_priest_with_evidence_fires_global_exposure(keep_with_managers: Any) -> None:
    """§9.8 — reporting the spy with valid proof trips the server-global exposure."""
    priest, _season = keep_with_managers
    priest.assign_spy()
    assert priest.exposed is False

    player = _make_player(_audience_room(), "unmasker-1")
    # One strong proof (the Detect Evil aura) is sufficient evidence to report.
    player.db.priest_evidence = {"strong_proofs": [priest_cfg.PROOF_DETECT_EVIL]}
    coin_before = int(player.db.coin or 0)
    try:
        _run(CmdAccept, player, EXPOSE_PRIEST)
        assert player.db.quests[EXPOSE_PRIEST]["state"] == "active"

        _run(CmdTurnin, player, EXPOSE_PRIEST)

        assert priest.exposed is True
        assert player.db.quests[EXPOSE_PRIEST]["state"] == "complete"
        assert int(player.db.coin or 0) == coin_before + 250
    finally:
        if player.pk is not None:
            player.delete()


@pytest.mark.django_db
def test_expose_priest_unavailable_without_evidence(keep_with_managers: Any) -> None:
    """§9.8 — the quest is evidence-gated: no proof, no commission, no exposure."""
    priest, _season = keep_with_managers
    priest.assign_spy()

    player = _make_player(_audience_room(), "unmasker-2")
    # A single clue sighting is suspicion, not proof — below the report threshold.
    player.db.priest_evidence = {"clue_sightings": ["black_candles"]}
    try:
        _run(CmdAccept, player, EXPOSE_PRIEST)
        # The Castellan refuses the commission; nothing is recorded.
        assert EXPOSE_PRIEST not in (player.db.quests or {})
        assert priest.exposed is False
    finally:
        if player.pk is not None:
            player.delete()


def _shrine_cleanser(room: Any) -> Any:
    """A player eligible for ``c_destroy_shrine`` (L7 + the minotaur prereq met)."""
    player = _make_player(room, "shrine-cleanser")
    player.traits.level.base = 7  # meets the quest's min_level
    # The quest requires the Shrine passage first won via the minotaur bounty.
    player.db.quests = {
        "g_minotaur": {
            "state": "complete",
            "progress": {},
            "times_completed": 1,
            "cooldown_until": 0.0,
        }
    }
    return player


@pytest.mark.django_db
def test_destroy_shrine_refused_without_the_deed(keep_with_managers: Any) -> None:
    """Exploit fix — accepting then immediately turning in c_destroy_shrine is refused.

    The deed (shattering the Altar) is a world event that has not happened, so the
    turn-in is held back: no reward, the quest stays active, and the season does NOT
    end (the season-ending trigger is the Altar hook, never the turn-in).
    """
    _priest, season = keep_with_managers
    player = _shrine_cleanser(_audience_room())
    coin_before = int(player.db.coin or 0)
    closing_season = season.db.season_number
    try:
        _run(CmdAccept, player, DESTROY_SHRINE)
        assert player.db.quests[DESTROY_SHRINE]["state"] == "active"

        _run(CmdTurnin, player, DESTROY_SHRINE)

        # Held back: still active, unpaid, and the season is untouched.
        assert player.db.quests[DESTROY_SHRINE]["state"] == "active"
        assert int(player.db.coin or 0) == coin_before
        assert season.db.season_number == closing_season
    finally:
        if player.pk is not None:
            player.delete()


@pytest.mark.django_db
def test_destroy_shrine_pays_reward_after_the_deed(keep_with_managers: Any) -> None:
    """§9.9 — once the shrine-destroyed deed flag is set, the turn-in pays its reward.

    Per review F4 the quest turn-in grants only the reward (1000 gp + the holy relic);
    the season-ending ``end_season`` is fired by the canonical ``Altar.at_destruction``
    hook, so the season counter does not advance from the turn-in itself.
    """
    _priest, season = keep_with_managers
    player = _shrine_cleanser(_audience_room())
    coin_before = int(player.db.coin or 0)
    closing_season = season.db.season_number
    try:
        _run(CmdAccept, player, DESTROY_SHRINE)
        # The Altar shattering (deferred world event) sets the deed flag.
        quests = dict(player.db.quests)
        assert qstate.record_deed(quests, DESTROY_SHRINE) is True
        player.db.quests = quests

        _run(CmdTurnin, player, DESTROY_SHRINE)

        assert player.db.quests[DESTROY_SHRINE]["state"] == "complete"
        assert int(player.db.coin or 0) == coin_before + 1000
        assert "a holy relic" in (player.db.quest_items or [])
        # The turn-in does not end the season — that is the Altar hook's job.
        assert season.db.season_number == closing_season
    finally:
        if player.pk is not None:
            player.delete()
