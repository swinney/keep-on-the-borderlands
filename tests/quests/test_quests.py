"""Behavior suite for the quest catalog (R9), per docs/specs/quests.md §9.

Every numbered §9 behavior has a test here. Pure state-machine and gating
behaviors run without a database; the cross-system *effect* behaviors boot
Django/Evennia (pytest-django) and exercise the turn-in command's effect path
(``_apply_reward`` / ``_apply_faction_effects`` / ``_advance_cult_chain`` /
``_fire_season_global``) directly. That is the appropriate level while
tribe-chief quest-givers and live mob spawning remain deferred (see tasks.md
"Deferred follow-ups"): the chief ``t_*`` quests have no in-game giver/turn-in
path yet, so their effects are verified at the wiring level rather than end to
end. Catalog data, prereq gating, and the season-global flow also have focused
suites (test_catalog.py, test_gating.py, test_season_global.py); this file is
the canonical §9 behavior checklist.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from evennia.utils import create
from evennia.utils.search import search_script

from commands.quests import CmdTurnin, _meets_evidence
from world.priest import config as priest_cfg
from world.quests import state as qstate
from world.quests.config import CATALOG

# ── §9.1-3, §9.10-11 — pure state machine + gating (no database) ──────────────


def test_quest_advances_through_steps() -> None:
    """§9.1 — WHEN each step is met THEN the quest completes and history bumps."""
    quest = CATALOG["g_kobold_cull"]  # kill 8 kobolds
    entry = qstate.accept(quest, None)
    assert entry["state"] == qstate.ACTIVE
    for _ in range(8):
        entry["progress"] = qstate.credit_kill(quest, entry["progress"], "kobold")
    assert qstate.steps_met(quest, entry["progress"])
    done = qstate.turn_in(quest, entry, now=1000.0)
    assert done["state"] == qstate.COMPLETE
    assert done["times_completed"] == 1


def test_prereqs_gate_availability() -> None:
    """§9.2 — WHEN the level prereq is unmet THEN the quest is not offered."""
    quest = CATALOG["g_orc_vile"]  # requires L2
    assert qstate.status(quest, None, level=1, now=0.0) == qstate.NOT_OFFERED
    assert qstate.status(quest, None, level=2, now=0.0) == qstate.AVAILABLE


def test_tribe_quest_requires_non_hostile_standing() -> None:
    """§9.5 — WHEN the player is hostile to the giver tribe THEN its quest is withheld."""
    quest = CATALOG["t_vol_vs_dec"]  # gates on orc_vol non-hostile
    hostile = qstate.status(quest, None, level=10, now=0.0, standings={"orc_vol": "hostile"})
    assert hostile == qstate.NOT_OFFERED
    neutral = qstate.status(quest, None, level=10, now=0.0, standings={"orc_vol": "neutral"})
    assert neutral == qstate.AVAILABLE


def test_repeatable_bounty_resets_after_cooldown() -> None:
    """§9.10 — WHEN a repeatable bounty's cooldown elapses THEN it is offered again."""
    quest = CATALOG["g_kobold_cull"]
    assert quest.repeatable
    done = qstate.turn_in(quest, qstate.accept(quest, None), now=1000.0)
    assert qstate.status(quest, done, level=10, now=1000.0) == qstate.COMPLETE  # on cooldown
    later = done["cooldown_until"] + 1
    assert qstate.status(quest, done, level=10, now=later) == qstate.AVAILABLE


def test_progress_resets_history_persists_on_season() -> None:
    """§9.11 — WHEN a completed quest is re-accepted THEN history persists, progress is fresh.

    Completion history (``times_completed``) is the per-character record that
    survives a season boundary; world-tied step progress is re-zeroed. ``accept``
    is the transition that carries the one and clears the other.
    """
    quest = CATALOG["g_kobold_cull"]
    done = qstate.turn_in(quest, qstate.accept(quest, None), now=1000.0)
    assert done["times_completed"] == 1
    reaccepted = qstate.accept(quest, done)
    assert reaccepted["times_completed"] == 1  # history persists
    assert reaccepted["progress"] == qstate.fresh_progress(quest)  # progress reset


# ── §9.3-4, §9.6-9 — cross-system effects on turn-in (engine) ─────────────────


@pytest.fixture
def managers_and_player() -> Iterator[tuple[Any, Any]]:
    """Boot the faction/priest/season managers + a bare player; tear all down."""
    factions = create.create_script("world.managers.faction_manager.FactionManager")
    priest = create.create_script("world.managers.priest_manager.PriestManager")
    season = create.create_script("world.managers.season_manager.SeasonManager")
    player = create.create_object("typeclasses.characters.PlayerCharacter", key="quester")
    try:
        yield factions, player
    finally:
        if player.pk is not None:
            player.delete()
        for script in (factions, priest, season):
            script.delete()


@pytest.mark.django_db
def test_rewards_grant_on_completion(managers_and_player: tuple[Any, Any]) -> None:
    """§9.3 — WHEN a quest is turned in THEN its gp/xp reward is paid."""
    _factions, player = managers_and_player
    quest = CATALOG["g_kobold_cull"]
    coin0 = int(player.db.coin or 0)
    xp0 = int(player.traits.xp.current)
    CmdTurnin()._apply_reward(player, quest)
    assert int(player.db.coin) == coin0 + quest.reward.gp
    assert int(player.traits.xp.current) == xp0 + quest.reward.xp


@pytest.mark.django_db
def test_item_reward_delivers_items(managers_and_player: tuple[Any, Any]) -> None:
    """§9.3 — WHEN an item-reward quest is turned in THEN its items are delivered.

    ``cu_holy_water`` rewards three vials of holy water; the items land on the caller's
    ``quest_items`` inventory list. A second item-reward turn-in appends rather
    than overwriting.
    """
    _factions, player = managers_and_player
    assert player.db.quest_items in (None, [])
    holy_water = CATALOG["cu_holy_water"]
    assert holy_water.reward.items == ("holy water", "holy water", "holy water")
    CmdTurnin()._apply_reward(player, holy_water)
    assert player.db.quest_items == ["holy water"] * 3
    # A further item reward appends to the existing inventory.
    CmdTurnin()._apply_reward(player, CATALOG["g_minotaur"])  # map to the Shrine
    assert player.db.quest_items == ["holy water"] * 3 + ["a map to the Shrine"]


@pytest.mark.django_db
def test_completion_applies_faction_standing(managers_and_player: tuple[Any, Any]) -> None:
    """§9.4 — WHEN an aiding/harming quest is turned in THEN standing shifts accordingly."""
    factions, player = managers_and_player
    pk = str(player.id)
    cmd = CmdTurnin()
    cmd._apply_faction_effects(player, CATALOG["c_rescue_soldier"])  # aid_faction="keep"
    assert factions.get_standing("keep", pk) > 0
    cmd._apply_faction_effects(player, CATALOG["g_kobold_cull"])  # harm_faction="kobold"
    assert factions.get_standing("kobold", pk) < 0


@pytest.mark.django_db
def test_tribe_quest_escalates_rivalry(managers_and_player: tuple[Any, Any]) -> None:
    """§9.5 — WHEN a tribe quest against a rival is turned in THEN pair tension rises."""
    factions, player = managers_and_player
    before = factions.get_tension("orc_vol", "orc_dec")
    CmdTurnin()._apply_faction_effects(player, CATALOG["t_vol_vs_dec"])
    assert factions.get_tension("orc_vol", "orc_dec") > before  # escalates toward war
    assert factions.get_standing("orc_vol", str(player.id)) > 0  # aid_faction="orc_vol"


@pytest.mark.django_db
def test_bribe_ogre_breaks_alliance(managers_and_player: tuple[Any, Any]) -> None:
    """§9.6 — WHEN the bribe-the-ogre quest is turned in THEN goblin↔ogre is no longer allied."""
    factions, player = managers_and_player
    assert factions.relation_band("goblin", "ogre") == "allied"  # initial bond
    CmdTurnin()._apply_faction_effects(player, CATALOG["t_bribe_ogre"])
    assert factions.relation_band("goblin", "ogre") != "allied"


@pytest.mark.django_db
def test_third_cult_quest_triggers_ambush(managers_and_player: tuple[Any, Any]) -> None:
    """§9.7 — WHEN a third cult-aiding quest is turned in THEN cult standing rises (ambush)."""
    factions, player = managers_and_player
    pk = str(player.id)
    cmd = CmdTurnin()
    cult_before = factions.get_standing(priest_cfg.CULT_FACTION_ID, pk)
    for quest_id in ("sp_package", "sp_reagent", "sp_minister"):
        cmd._advance_cult_chain(player, CATALOG[quest_id])
    assert player.db.spy_quests == sorted(["sp_package", "sp_reagent", "sp_minister"])
    # The third completion brands the collaborator: cult standing has risen.
    assert factions.get_standing(priest_cfg.CULT_FACTION_ID, pk) > cult_before


@pytest.mark.django_db
def test_expose_priest_is_evidence_gated(managers_and_player: tuple[Any, Any]) -> None:
    """§9.8 — WHEN expose-priest is turned in THEN it fires only with sufficient evidence."""
    _factions, player = managers_and_player
    priest = search_script("priest_manager")[0]
    priest.assign_spy()
    cmd = CmdTurnin()
    quest = CATALOG["c_expose_priest"]

    player.db.priest_evidence = {"clue_sightings": ["black_candles"]}  # suspicion, not proof
    assert cmd._fire_season_global(player, quest) is False
    assert priest.exposed is False

    player.db.priest_evidence = {"strong_proofs": [priest_cfg.PROOF_DETECT_EVIL]}
    assert cmd._fire_season_global(player, quest) is True
    assert priest.exposed is True


@pytest.mark.django_db
def test_evidence_grades_gate_per_quest(managers_and_player: tuple[Any, Any]) -> None:
    """§9.2/§9.8 — WHEN evidence is partial THEN each quest applies its own bar.

    The two evidence-gated quests do not share one global threshold: the Curate's
    doubt (``cu_suspicions``) opens at the lower ``CURATE_CLUE_THRESHOLD`` clue
    sightings while exposing the spy (``c_expose_priest``) demands report-grade
    proof (one strong proof or ``CLUE_SIGHTINGS_TO_REPORT`` sightings).
    """
    _factions, player = managers_and_player
    suspicions = CATALOG["cu_suspicions"]  # EVIDENCE_CURATE
    expose = CATALOG["c_expose_priest"]  # EVIDENCE_REPORT

    # No evidence → neither bar is met.
    player.db.priest_evidence = {}
    assert _meets_evidence(player, suspicions) is False
    assert _meets_evidence(player, expose) is False

    # Exactly the Curate threshold of distinct sightings → the Curate opens up,
    # but that is still short of report-grade, so exposing stays gated.
    assert priest_cfg.CURATE_CLUE_THRESHOLD == 2
    assert priest_cfg.CLUE_SIGHTINGS_TO_REPORT == 3
    player.db.priest_evidence = {"clue_sightings": ["black_candles", "hooded_meeting"]}
    assert _meets_evidence(player, suspicions) is True
    assert _meets_evidence(player, expose) is False

    # A third distinct sighting reaches report-grade → both open.
    player.db.priest_evidence = {
        "clue_sightings": ["black_candles", "hooded_meeting", "midnight_errand"]
    }
    assert _meets_evidence(player, suspicions) is True
    assert _meets_evidence(player, expose) is True

    # A single strong proof is report-grade, so exposing opens — but the Curate
    # gate is defined strictly on *clue sightings* (spec §3), which a lone proof
    # does not supply, so her doubt stays shut.
    player.db.priest_evidence = {"strong_proofs": [priest_cfg.PROOF_DETECT_EVIL]}
    assert _meets_evidence(player, suspicions) is False
    assert _meets_evidence(player, expose) is True


@pytest.mark.django_db
def test_destroy_shrine_ends_season(managers_and_player: tuple[Any, Any]) -> None:
    """§9.9 — WHEN destroy-Shrine is turned in THEN the season ends early."""
    _factions, player = managers_and_player
    season = search_script("season_manager")[0]
    closing = season.db.season_number
    assert CmdTurnin()._fire_season_global(player, CATALOG["c_destroy_shrine"]) is True
    assert season.db.season_number == closing + 1
