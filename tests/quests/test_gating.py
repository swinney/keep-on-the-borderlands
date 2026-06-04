"""Pure-core tests for M13 prereq gating + per-character story/repeatable state.

Covers the "Faction gating + repeatable/story state per character" slice of the
quest catalog (docs/specs/quests.md §1, §6, §9.2/§9.5/§9.10): the per-character
state machine withholds a quest until its level, prior-quest, faction-standing,
and evidence prerequisites all clear, and it keeps story quests ``complete`` while
reopening repeatable bounties only once their cooldown elapses *and* their
prereqs still hold.

Exercised without booting Evennia (no DB fixture requested).
"""

from __future__ import annotations

from world.quests import state as qstate
from world.quests.config import CATALOG, StandingGate


def _complete(quest_id: str) -> qstate.QuestEntry:
    """A stored ``complete`` entry for ``quest_id`` (cooldown already elapsed)."""
    quest = CATALOG[quest_id]
    return {
        "state": qstate.COMPLETE,
        "progress": qstate.fresh_progress(quest),
        "times_completed": 1,
        "cooldown_until": 0.0,
    }


# ── default standing band matches the faction ladder ─────────────────────────


def test_default_standing_band_is_non_hostile() -> None:
    # A fresh (faction, player) pair sits at reputation 0 → neutral, which clears
    # the tribe-chief "non-hostile" gate.
    assert qstate.DEFAULT_STANDING_BAND == "neutral"


# ── level gate (quests.md §1) ────────────────────────────────────────────────


def test_level_gate_withholds_until_min_level() -> None:
    minotaur = CATALOG["g_minotaur"]  # min_level 5
    assert not qstate.prereqs_met(minotaur, level=4)
    assert qstate.prereqs_met(minotaur, level=5)
    assert qstate.prereqs_met(minotaur, level=9)


def test_status_reflects_level_gate_with_no_entry() -> None:
    minotaur = CATALOG["g_minotaur"]
    assert qstate.status(minotaur, None, level=4, now=0.0) == qstate.NOT_OFFERED
    assert qstate.status(minotaur, None, level=5, now=0.0) == qstate.AVAILABLE


# ── prior-quest gate (quests.md §1, §7) ──────────────────────────────────────


def test_prior_quest_gate_blocks_until_predecessor_complete() -> None:
    reagent = CATALOG["sp_reagent"]  # prereq: sp_package
    # No log → predecessor not complete → gated.
    assert not qstate.prereqs_met(reagent, level=1)
    assert not qstate.prereqs_met(reagent, level=1, log={})
    # Predecessor merely accepted (active) is not enough.
    active_pkg = {"sp_package": qstate.accept(CATALOG["sp_package"], None)}
    assert not qstate.prereqs_met(reagent, level=1, log=active_pkg)
    # Predecessor complete → opens.
    done_pkg = {"sp_package": _complete("sp_package")}
    assert qstate.prereqs_met(reagent, level=1, log=done_pkg)


def test_chain_opens_one_link_at_a_time() -> None:
    minister = CATALOG["sp_minister"]  # prereq: sp_reagent
    # sp_package done but sp_reagent not → minister still gated.
    log = {"sp_package": _complete("sp_package")}
    assert not qstate.prereqs_met(minister, level=1, log=log)
    log["sp_reagent"] = _complete("sp_reagent")
    assert qstate.prereqs_met(minister, level=1, log=log)


def test_story_quest_combines_level_and_prior_quest() -> None:
    shrine = CATALOG["c_destroy_shrine"]  # min_level 7, prereq g_minotaur
    done_mino = {"g_minotaur": _complete("g_minotaur")}
    assert not qstate.prereqs_met(shrine, level=7)  # prereq quest missing
    assert not qstate.prereqs_met(shrine, level=6, log=done_mino)  # level short
    assert qstate.prereqs_met(shrine, level=7, log=done_mino)


# ── faction-standing gate (quests.md §6, §9.5) ───────────────────────────────


def test_tribe_chief_quest_offered_at_default_neutral_standing() -> None:
    vol = CATALOG["t_vol_vs_dec"]  # gate: orc_vol >= neutral
    # No standings recorded → default neutral → offered.
    assert qstate.prereqs_met(vol, level=1)
    assert qstate.prereqs_met(vol, level=1, standings={})
    assert qstate.prereqs_met(vol, level=1, standings={"orc_vol": "friendly"})


def test_tribe_chief_quest_withheld_at_hostile_standing() -> None:
    vol = CATALOG["t_vol_vs_dec"]
    assert not qstate.prereqs_met(vol, level=1, standings={"orc_vol": "hostile"})
    assert not qstate.prereqs_met(vol, level=1, standings={"orc_vol": "kill-on-sight"})


def test_status_withdraws_chief_quest_once_player_turns_hostile() -> None:
    vol = CATALOG["t_vol_vs_dec"]
    friendly = {"orc_vol": "neutral"}
    hostile = {"orc_vol": "hostile"}
    assert qstate.status(vol, None, level=1, now=0.0, standings=friendly) == qstate.AVAILABLE
    assert qstate.status(vol, None, level=1, now=0.0, standings=hostile) == qstate.NOT_OFFERED


def test_standing_gate_only_constrains_the_named_faction() -> None:
    vol = CATALOG["t_vol_vs_dec"]  # gates only on orc_vol
    # Hostility to an *unrelated* tribe does not withhold the orc_vol chief's quest.
    assert qstate.prereqs_met(vol, level=1, standings={"goblin": "kill-on-sight"})


def test_standing_ok_helper_ranks_against_the_ladder() -> None:
    gate = StandingGate(faction="goblin", min_band="neutral")
    assert qstate.standing_ok(gate, {"goblin": "neutral"})
    assert qstate.standing_ok(gate, {"goblin": "friendly"})
    assert not qstate.standing_ok(gate, {"goblin": "hostile"})
    assert not qstate.standing_ok(gate, {"goblin": "kill-on-sight"})
    # Unknown faction defaults to neutral → clears a neutral gate.
    assert qstate.standing_ok(gate, {})


# ── evidence gate (quests.md §3, §4, R4) ─────────────────────────────────────


def test_evidence_gated_quests_need_proof() -> None:
    for qid in ("c_expose_priest", "cu_suspicions"):
        quest = CATALOG[qid]
        assert not qstate.prereqs_met(quest, level=1)
        assert not qstate.prereqs_met(quest, level=1, has_evidence=False)
        assert qstate.prereqs_met(quest, level=1, has_evidence=True)


def test_status_gates_expose_priest_on_evidence() -> None:
    expose = CATALOG["c_expose_priest"]
    assert qstate.status(expose, None, level=1, now=0.0) == qstate.NOT_OFFERED
    assert qstate.status(expose, None, level=1, now=0.0, has_evidence=True) == qstate.AVAILABLE


# ── repeatable vs story state, per character (quests.md §1, §9.10) ────────────


def test_story_quest_stays_complete_and_never_reopens() -> None:
    rescue = CATALOG["c_rescue_soldier"]  # not repeatable
    assert rescue.repeatable is False
    done: qstate.QuestEntry = {
        "state": qstate.COMPLETE,
        "progress": {},
        "times_completed": 1,
        "cooldown_until": 0.0,
    }
    # Even far in the future and with prereqs met, a story quest stays complete.
    assert qstate.status(rescue, done, level=9, now=1.0e9) == qstate.COMPLETE
    assert not qstate.can_accept(rescue, done, level=9, now=1.0e9)


def test_repeatable_bounty_reopens_only_when_prereqs_still_hold() -> None:
    vol = CATALOG["g_orc_vile"]  # repeatable, min_level 2
    completed: qstate.QuestEntry = {
        "state": qstate.COMPLETE,
        "progress": qstate.fresh_progress(vol),
        "times_completed": 3,
        "cooldown_until": 1000.0,
    }
    # Cooldown elapsed and level still met → reopens.
    assert qstate.status(vol, completed, level=2, now=1000.0) == qstate.AVAILABLE
    # Cooldown elapsed but (hypothetically) under-level → does not reopen.
    assert qstate.status(vol, completed, level=1, now=1000.0) == qstate.NOT_OFFERED
    assert not qstate.can_accept(vol, completed, level=1, now=1000.0)


def test_completion_history_is_preserved_per_character_on_reaccept() -> None:
    vol = CATALOG["g_orc_vile"]
    completed: qstate.QuestEntry = {
        "state": qstate.COMPLETE,
        "progress": qstate.fresh_progress(vol),
        "times_completed": 4,
        "cooldown_until": 0.0,
    }
    reaccepted = qstate.accept(vol, completed)
    assert reaccepted["state"] == qstate.ACTIVE
    assert reaccepted["times_completed"] == 4  # history carried across re-accept
    assert reaccepted["progress"] == qstate.fresh_progress(vol)
