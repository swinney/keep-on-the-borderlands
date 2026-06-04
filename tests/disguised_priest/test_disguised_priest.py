"""Tests for the disguised priest plot (R4).

Derived from openspec/changes/b2-mud-v1-design/specs/disguised-priest/spec.md and
docs/specs/disguised-priest.md §7.

This file covers the pure rotation core (PriestState): the seasonal identity and
the no-back-to-back guarantee (behaviors 1-2). The remaining M12 behaviors —
clue assignment, the four detection paths, the spy quest chain, exposure, and
reset — land with their own slices and unskip the stubs below as they arrive.
"""

from random import Random

import pytest

from world.priest import config as cfg
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


# ── Later M12 slices unskip these as they land ────────────────────────────────


@pytest.mark.skip(reason="M12 detection-paths slice")
def test_detect_evil_distinguishes_spy() -> None:
    """WHEN Detect Evil hits the spy vs an innocent THEN only the spy yields proof."""


@pytest.mark.skip(reason="M12 detection-paths slice")
def test_witnessing_night_act_logs_clue() -> None:
    """WHEN a player witnesses the night tell THEN a clue sighting logs for them."""


@pytest.mark.skip(reason="M12 detection-paths slice")
def test_searching_finds_planted_object() -> None:
    """WHEN a player searches the spy's cell THEN the planted clue object is found."""


@pytest.mark.skip(reason="M12 detection-paths slice")
def test_curate_branch_gates_on_two_clues() -> None:
    """WHEN a player has fewer than two clue sightings THEN the Curate stays silent."""


@pytest.mark.skip(reason="M12 detection-paths slice")
def test_evidence_is_per_character() -> None:
    """WHEN one player gathers evidence THEN another player's evidence is unaffected."""


@pytest.mark.skip(reason="M12 spy-quest-chain slice")
def test_three_spy_quests_trigger_ambush() -> None:
    """WHEN a player completes a third spy quest THEN a Caves ambush fires and cult standing rises."""


@pytest.mark.skip(reason="M12 exposure slice")
def test_valid_report_exposes_and_relocates() -> None:
    """WHEN a player reports with sufficient evidence THEN exposed is set and the spy becomes a boss."""


@pytest.mark.skip(reason="M12 exposure slice")
def test_weak_report_is_rejected() -> None:
    """WHEN a player reports without enough evidence THEN the report is rejected."""


@pytest.mark.skip(reason="M12 reset slice")
def test_reset_clears_plot() -> None:
    """WHEN a season resets THEN identity re-rolls, exposure/evidence clear, chapel restores."""
