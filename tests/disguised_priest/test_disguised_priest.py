"""Phase 0 test stubs for the disguised priest plot (R4).

Derived from openspec/changes/b2-mud-v1-design/specs/disguised-priest/spec.md and
docs/specs/disguised-priest.md §7. Docstring-only; Phase 2 unskips and implements.
"""

import pytest

pytestmark = pytest.mark.skip(reason="Phase 0 stub — implementation in Phase 2")


def test_exactly_one_spy_per_season() -> None:
    """WHEN a season begins THEN exactly one chapel NPC is the spy."""


def test_spy_never_repeats_back_to_back() -> None:
    """WHEN two consecutive seasons begin THEN the spy NPC differs."""


def test_clue_set_drawn_and_attached() -> None:
    """WHEN a season begins THEN CLUE_COUNT distinct clues attach to the spy."""


def test_two_resets_yield_different_identity_and_clues() -> None:
    """WHEN two resets occur THEN identity differs and the clue set is re-drawn."""


def test_detect_evil_distinguishes_spy() -> None:
    """WHEN Detect Evil hits the spy vs an innocent THEN only the spy yields proof."""


def test_witnessing_night_act_logs_clue() -> None:
    """WHEN a player witnesses the night tell THEN a clue sighting logs for them."""


def test_searching_finds_planted_object() -> None:
    """WHEN a player searches the spy's cell THEN the planted clue object is found."""


def test_curate_branch_gates_on_two_clues() -> None:
    """WHEN a player has fewer than two clue sightings THEN the Curate stays silent."""


def test_evidence_is_per_character() -> None:
    """WHEN one player gathers evidence THEN another player's evidence is unaffected."""


def test_three_spy_quests_trigger_ambush() -> None:
    """WHEN a player completes a third spy quest THEN a Caves ambush fires and cult standing rises."""


def test_valid_report_exposes_and_relocates() -> None:
    """WHEN a player reports with sufficient evidence THEN exposed is set and the spy becomes a boss."""


def test_weak_report_is_rejected() -> None:
    """WHEN a player reports without enough evidence THEN the report is rejected."""


def test_reset_clears_plot() -> None:
    """WHEN a season resets THEN identity re-rolls, exposure/evidence clear, chapel restores."""
