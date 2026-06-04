"""Tests for the disguised priest plot (R4).

Derived from openspec/changes/b2-mud-v1-design/specs/disguised-priest/spec.md and
docs/specs/disguised-priest.md §7.

This file covers the pure rotation core (PriestState): the seasonal identity and
the no-back-to-back guarantee (behaviors 1-2). The remaining M12 behaviors —
clue assignment, the four detection paths, the spy quest chain, exposure, and
reset — land with their own slices and unskip the stubs below as they arrive.
"""

from random import Random

from world.factions.state import FactionState
from world.priest import config as cfg
from world.priest import detection, exposure, quests
from world.priest.evidence import Evidence
from world.priest.quests import SpyQuestLog
from world.priest.state import PriestState


def test_exactly_one_spy_per_season() -> None:
    """WHEN a season begins THEN exactly one chapel NPC is the spy."""
    state = PriestState()
    spy = state.assign_spy(Random(1))
    assert spy in cfg.POOL_IDS
    assert state.spy_id == spy
    # Exactly one of the pool is the spy: the rest are not.
    assert sum(1 for npc_id in cfg.POOL_IDS if npc_id == state.spy_id) == 1


def test_spy_never_repeats_back_to_back() -> None:
    """WHEN two consecutive seasons begin THEN the spy NPC differs."""
    rng = Random(20260604)
    state = PriestState()
    previous = state.assign_spy(rng)
    # Many rotations across many seeds — every consecutive pair must differ.
    for _ in range(200):
        current = state.assign_spy(rng)
        assert current != previous
        assert current in cfg.POOL_IDS
        previous = current


def test_first_assignment_may_be_any_pool_member() -> None:
    """WHEN the very first spy is rolled THEN the whole pool is eligible."""
    seen: set[str] = set()
    for seed in range(100):
        seen.add(PriestState().assign_spy(Random(seed)))
    assert seen == set(cfg.POOL_IDS)


# ── Clue assignment (spec §2 step 2, §7 behaviors 3-4) ────────────────────────


def test_clue_set_drawn_and_attached() -> None:
    """WHEN a season begins THEN CLUE_COUNT distinct clues attach to the spy."""
    state = PriestState()
    state.assign_spy(Random(1))
    clues = state.assign_clues(Random(1))
    # The draw is CLUE_COUNT distinct clues, all from the pool, and is what the
    # state now holds as the spy's attached set.
    assert len(clues) == cfg.CLUE_COUNT
    assert len(set(clues)) == cfg.CLUE_COUNT
    assert set(clues) <= set(cfg.CLUE_IDS)
    assert state.clue_ids == clues


def test_clue_draw_is_unbiased_over_the_pool() -> None:
    """WHEN clues are drawn across many seeds THEN every pool clue can appear."""
    seen: set[str] = set()
    for seed in range(100):
        state = PriestState()
        seen.update(state.assign_clues(Random(seed)))
    assert seen == set(cfg.CLUE_IDS)


def test_two_resets_yield_different_identity_and_clues() -> None:
    """WHEN two resets occur THEN identity differs and the clue set is re-drawn."""
    rng = Random(20260604)
    state = PriestState()
    state.assign_spy(rng)
    state.assign_clues(rng)
    first_spy, first_clues = state.spy_id, state.clue_ids

    state.assign_spy(rng)
    new_clues = state.assign_clues(rng)

    # Identity never repeats back-to-back, and the clue set is a fresh valid draw.
    assert state.spy_id != first_spy
    assert len(new_clues) == cfg.CLUE_COUNT
    assert len(set(new_clues)) == cfg.CLUE_COUNT
    assert set(new_clues) <= set(cfg.CLUE_IDS)
    # The re-draw replaced the prior set rather than retaining it by reference.
    assert state.clue_ids == new_clues
    assert state.clue_ids != first_clues


# ── Detection paths (spec §3, §7 behaviors 5-9) ───────────────────────────────


def test_detect_evil_distinguishes_spy() -> None:
    """WHEN Detect Evil hits the spy vs an innocent THEN only the spy yields proof."""
    spy = "ortho"
    innocent = "anselm"
    state = PriestState(spy_id=spy)
    level = cfg.DETECT_EVIL_MIN_LEVEL

    # The spy radiates an evil aura — a strong proof; the innocent shows nothing.
    spy_ev = Evidence()
    assert detection.detect_evil(state, spy, level, spy_ev) is True
    assert spy_ev.strong_proofs == {cfg.PROOF_DETECT_EVIL}
    assert spy_ev.can_report is True

    innocent_ev = Evidence()
    assert detection.detect_evil(state, innocent, level, innocent_ev) is False
    assert innocent_ev.strong_proofs == set()
    assert innocent_ev.can_report is False


def test_detect_evil_requires_sufficient_caster_level() -> None:
    """WHEN a too-low cleric casts Detect Evil on the spy THEN no aura shows."""
    state = PriestState(spy_id="ortho")
    ev = Evidence()
    assert detection.detect_evil(state, "ortho", cfg.DETECT_EVIL_MIN_LEVEL - 1, ev) is False
    assert ev.strong_proofs == set()


def test_witnessing_night_act_logs_clue() -> None:
    """WHEN a player witnesses the night tell THEN a clue sighting logs for them."""
    # black_candles is a night_act clue; attach it to this season's spy.
    state = PriestState(spy_id="ortho", clue_ids=("black_candles", "holy_water"))
    ev = Evidence()

    # By day the act does not occur, so nothing is observed.
    assert detection.witness_night_act(state, "black_candles", ev, is_night=False) is False
    assert ev.clue_count == 0

    # At game-night a present player observes it and logs the sighting.
    assert detection.witness_night_act(state, "black_candles", ev, is_night=True) is True
    assert ev.clue_sightings == {"black_candles"}

    # Re-witnessing the same act does not inflate the sighting count.
    assert detection.witness_night_act(state, "black_candles", ev, is_night=True) is False
    assert ev.clue_count == 1


def test_witnessing_ignores_non_spy_or_non_night_clues() -> None:
    """WHEN the clue is not a spy night-act tell THEN nothing is logged."""
    state = PriestState(spy_id="ortho", clue_ids=("black_candles", "holy_water"))
    ev = Evidence()

    # holy_water is attached but is an 'observed' tell, not a night act.
    assert detection.witness_night_act(state, "holy_water", ev, is_night=True) is False
    # hooded_visitor is a night act but is NOT this spy's clue this season.
    assert detection.witness_night_act(state, "hooded_visitor", ev, is_night=True) is False
    assert ev.clue_count == 0


def test_searching_finds_planted_object() -> None:
    """WHEN a player searches the spy's cell THEN the planted clue object is found."""
    # black_dagger is a planted object that is suggestive, not conclusive.
    state = PriestState(spy_id="maeve", clue_ids=("black_dagger", "holy_water"))
    ev = Evidence()
    found = detection.search_for_object(state, ev)
    assert found == "black_dagger"
    assert ev.clue_sightings == {"black_dagger"}
    assert ev.strong_proofs == set()
    assert ev.can_report is False  # one sighting is not enough on its own


def test_searching_a_smoking_gun_yields_strong_proof() -> None:
    """WHEN the planted object is itself proof THEN searching yields a strong proof."""
    # shrine_password is a planted object flagged is_proof.
    state = PriestState(spy_id="maeve", clue_ids=("shrine_password", "holy_water"))
    ev = Evidence()
    found = detection.search_for_object(state, ev)
    assert found == "shrine_password"
    assert ev.strong_proofs == {"shrine_password"}
    assert ev.clue_sightings == set()
    assert ev.can_report is True


def test_searching_finds_nothing_without_a_planted_tell() -> None:
    """WHEN the spy has no planted object THEN a search turns up nothing."""
    state = PriestState(spy_id="ortho", clue_ids=("black_candles", "holy_water"))
    ev = Evidence()
    assert detection.search_for_object(state, ev) is None
    assert ev.clue_count == 0
    assert ev.strong_proofs == set()


def test_curate_branch_gates_on_two_clues() -> None:
    """WHEN a player has fewer than two clue sightings THEN the Curate stays silent."""
    state = PriestState(
        spy_id="bellan",
        clue_ids=("black_candles", "holy_water", "omits_litany"),
    )

    # Below the threshold the Curate shares nothing and logs nothing.
    ev = Evidence(clue_sightings=("black_candles",))
    assert detection.curate_dialogue(state, ev) is None
    assert ev.clue_count == 1

    # At the threshold the Curate names a not-yet-seen clue, logging it.
    ev2 = Evidence(clue_sightings=("black_candles", "holy_water"))
    hint = detection.curate_dialogue(state, ev2)
    assert hint == "omits_litany"
    assert hint in ev2.clue_sightings
    assert ev2.clue_count == 3


def test_curate_silent_when_all_clues_already_seen() -> None:
    """WHEN the player already knows every clue THEN the Curate adds nothing new."""
    state = PriestState(spy_id="bellan", clue_ids=("black_candles", "holy_water"))
    ev = Evidence(clue_sightings=("black_candles", "holy_water"))
    assert detection.curate_dialogue(state, ev) is None
    assert ev.clue_count == 2


def test_evidence_is_per_character() -> None:
    """WHEN one player gathers evidence THEN another player's evidence is unaffected."""
    state = PriestState(spy_id="ortho", clue_ids=("black_candles", "black_dagger"))
    alice = Evidence()
    bob = Evidence()

    # Alice investigates; Bob does nothing.
    detection.witness_night_act(state, "black_candles", alice, is_night=True)
    detection.search_for_object(state, alice)

    assert alice.clue_sightings == {"black_candles", "black_dagger"}
    assert bob.clue_sightings == set()
    assert bob.clue_count == 0


# ── Spy quest chain (spec §4, §7 behavior 10) ─────────────────────────────────


def test_three_spy_quests_trigger_ambush() -> None:
    """WHEN a player completes a third spy quest THEN a Caves ambush fires and cult standing rises."""
    log = SpyQuestLog()

    # The first two aids_cult quests are benign-seeming: no ambush yet.
    assert quests.complete_spy_quest(log, "deliver_sealed_package") is False
    assert quests.complete_spy_quest(log, "minister_to_cultist") is False
    assert log.completed_count == 2
    assert log.ambush_sprung is False

    # The third distinct spy quest springs the scripted Caves ambush.
    assert quests.complete_spy_quest(log, "fetch_poison_herb") is True
    assert log.ambush_sprung is True
    assert log.completed_count == 3

    # The ambush fires exactly once: a fourth quest does not re-trigger it.
    assert quests.complete_spy_quest(log, "fourth_errand") is False
    assert log.ambush_sprung is True

    # Branded a cult collaborator: the consequence raises cult standing (R2).
    fac = FactionState()
    assert fac.get_standing(cfg.CULT_FACTION_ID, "alice") == 0
    fac.apply_quest_aid(cfg.CULT_FACTION_ID, "alice")
    assert fac.get_standing(cfg.CULT_FACTION_ID, "alice") > 0


def test_spy_quest_log_ignores_repeat_completions() -> None:
    """WHEN the same spy quest is turned in twice THEN it counts once toward the ambush."""
    log = SpyQuestLog()
    assert quests.complete_spy_quest(log, "deliver_sealed_package") is False
    # Re-turning the same quest does not advance the chain.
    assert quests.complete_spy_quest(log, "deliver_sealed_package") is False
    assert log.completed_count == 1
    assert log.ambush_sprung is False


def test_spy_quest_log_is_per_character() -> None:
    """WHEN one player collaborates THEN another player's chain is unaffected."""
    alice = SpyQuestLog()
    bob = SpyQuestLog()

    quests.complete_spy_quest(alice, "deliver_sealed_package")
    quests.complete_spy_quest(alice, "minister_to_cultist")
    quests.complete_spy_quest(alice, "fetch_poison_herb")

    assert alice.ambush_sprung is True
    assert bob.completed_count == 0
    assert bob.ambush_sprung is False


# ── Exposure (spec §5, §7 behaviors 11-12) ────────────────────────────────────


def test_valid_report_exposes_and_relocates() -> None:
    """WHEN a player reports with sufficient evidence THEN exposed is set and the spy becomes a boss."""
    state = PriestState(spy_id="ortho", clue_ids=("black_candles", "holy_water"))
    assert state.exposed is False

    # A single strong proof is sufficient to report; the report returns the spy
    # id to relocate to the Shrine as a boss (spec §5 step 3) and trips the
    # server-global exposed flag.
    ev = Evidence(strong_proofs=(cfg.PROOF_DETECT_EVIL,))
    assert ev.can_report is True
    assert exposure.report_to_castellan(state, ev) == "ortho"
    assert state.exposed is True


def test_three_sightings_also_expose() -> None:
    """WHEN a player reports with three clue sightings THEN exposure fires."""
    state = PriestState(
        spy_id="bellan",
        clue_ids=("black_candles", "holy_water", "omits_litany"),
    )
    # Three distinct sightings (no strong proof) clear the report bar (spec §3).
    ev = Evidence(clue_sightings=("black_candles", "holy_water", "omits_litany"))
    assert ev.can_report is True
    assert exposure.report_to_castellan(state, ev) == "bellan"
    assert state.exposed is True


def test_exposure_is_global_and_fires_once() -> None:
    """WHEN the spy is already exposed THEN a later report does not re-fire the event."""
    state = PriestState(spy_id="ortho", clue_ids=("black_candles",))
    first = Evidence(strong_proofs=(cfg.PROOF_DETECT_EVIL,))
    assert exposure.report_to_castellan(state, first) == "ortho"
    assert state.exposed is True

    # A second reporter, even with their own valid evidence, finds the secret
    # already public: the world event is a one-shot, so the report is a no-op.
    second = Evidence(clue_sightings=("black_candles", "holy_water", "omits_litany"))
    assert second.can_report is True
    assert exposure.report_to_castellan(state, second) is None
    assert state.exposed is True


def test_weak_report_is_rejected() -> None:
    """WHEN a player reports without enough evidence THEN the report is rejected."""
    state = PriestState(spy_id="ortho", clue_ids=("black_candles", "holy_water"))

    # One clue sighting is short of the three-sighting bar and is no strong
    # proof: the report is rejected ("suspicions, not proof") and nothing is
    # exposed.
    ev = Evidence(clue_sightings=("black_candles",))
    assert ev.can_report is False
    assert exposure.report_to_castellan(state, ev) is None
    assert state.exposed is False


def test_reset_clears_plot() -> None:
    """WHEN a season resets THEN identity re-rolls, exposure/evidence clear, chapel restores."""
    rng = Random(20260604)
    state = PriestState()
    state.assign_spy(rng)
    state.assign_clues(rng)

    # Expose the spy this season, and have a player accrue some evidence.
    proof = Evidence(strong_proofs=(cfg.PROOF_DETECT_EVIL,))
    exposure.report_to_castellan(state, proof)
    assert state.exposed is True
    first_spy, first_clues = state.spy_id, state.clue_ids

    # The season boundary reset re-rolls the whole plot in one transition.
    new_spy, new_clues = state.reset_season(rng)

    # Identity re-rolls and never repeats the just-ended season's spy.
    assert new_spy == state.spy_id
    assert state.spy_id != first_spy
    assert state.spy_id in cfg.POOL_IDS

    # The clue set is a fresh valid draw, not last season's.
    assert new_clues == state.clue_ids
    assert len(state.clue_ids) == cfg.CLUE_COUNT
    assert len(set(state.clue_ids)) == cfg.CLUE_COUNT
    assert set(state.clue_ids) <= set(cfg.CLUE_IDS)
    assert state.clue_ids != first_clues

    # Exposure is cleared: the new season's spy starts unmasked, and a reporter
    # who still held last season's proof can no longer expose without re-earning
    # it against this season's identity (the flag is fresh, evidence is private).
    assert state.exposed is False

    # Per-character evidence lives off the global state, so a new season's
    # investigator starts from an empty Evidence — nothing carries over.
    fresh = Evidence()
    assert fresh.clue_count == 0
    assert fresh.strong_proofs == set()
    assert fresh.can_report is False


def test_two_season_rotation_full_cycle() -> None:
    """WHEN two full seasons run THEN each rotates identity, clues, and exposure cleanly."""
    rng = Random(7)
    state = PriestState()

    # Season 1: assign, expose.
    state.reset_season(rng)
    season1_spy = state.spy_id
    assert season1_spy in cfg.POOL_IDS
    exposure.report_to_castellan(state, Evidence(strong_proofs=(cfg.PROOF_DETECT_EVIL,)))
    assert state.exposed is True

    # Season 2: reset rotates to a different spy and clears the prior exposure.
    state.reset_season(rng)
    season2_spy = state.spy_id
    assert season2_spy != season1_spy
    assert season2_spy in cfg.POOL_IDS
    assert state.exposed is False
    assert len(state.clue_ids) == cfg.CLUE_COUNT
