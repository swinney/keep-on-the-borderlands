"""Full acceptance-criteria coverage checklist (acceptance.md §4, §6.4).

The OpenSpec prompt lists **eight** testable acceptance criteria (C1-C8). This
module is the capstone that turns "all acceptance criteria demonstrably met" from
prose into a machine-checked invariant: it encodes the §4 table as **data**
(criterion id → the proof test node id(s) that demonstrate it) and asserts, for
each, that the named proof test **exists and is collectable**. If a referenced
proof is renamed away or deleted, the coverage test fails — flagging that a
criterion lost its proof.

**What this does and does not do (honesty — acceptance.md §4.1, §5):** the
coverage test *references* the existing subsystem suites; it does **not** re-run or
duplicate their behaviour (C1-C7 are proven by their own suites, which M16 does not
modify; C8 by the M16 latency test in this same suite). Collectability is checked
statically — the proof file is parsed and the named module-level test function is
confirmed defined — so this check is pure/Django-free and does not import the
engine test modules (which would boot Evennia). A static "function is defined at
module level under a ``test_*.py`` file in ``tests/``" check is the durable proxy
for "pytest can collect it": it catches the rename/deletion regression the spec
calls for without paying an engine boot.

The ``CRITERIA`` table below is the single authoritative list of "what 'done' means
for v1 acceptance," kept in one place for review.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import pytest

# Repository root: this file is ``<root>/tests/acceptance/test_criteria_coverage.py``.
REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Criterion:
    """One OpenSpec acceptance criterion and the proof test node ids for it."""

    id: str
    description: str
    proofs: tuple[str, ...]


# ── The §4 acceptance-criteria coverage table, as data ───────────────────────────
# Each proof is a pytest node id ``<path-from-repo-root>::<test function>``. The
# picks are representative, directly-demonstrating nodes from each criterion's
# suite (not the whole suite) so a reviewer sees exactly which test proves what.
CRITERIA: tuple[Criterion, ...] = (
    Criterion(
        "C1",
        "New char spawns at Keep → equips → hires → travels → clears a tribe "
        "quest → returns and turns it in (M9 vertical slice).",
        ("tests/zones/test_m9_vertical_slice.py::test_kobold_cave_vertical_slice",),
    ),
    Criterion(
        "C2",
        "Faction state transitions from scripted player actions, observed in NPC "
        "behaviour (tests/faction + the M9 standing-shift, M4 ↔ M9).",
        (
            "tests/faction/test_faction.py::test_five_kills_make_standing_hostile",
            "tests/faction/test_faction.py::test_killing_members_thaws_only_tense_or_war_rivals",
            "tests/zones/test_m9_vertical_slice.py::test_kobold_cave_vertical_slice",
        ),
    ),
    Criterion(
        "C3",
        "Tribe-scoped repop halt and rival-tribe expansion both fire under test "
        "(tests/repop + world-build §13.5 leadership-halt-with-real-scouts).",
        (
            "tests/repop/test_repop.py::test_both_leaders_dead_triggers_halt",
            "tests/repop/test_repop.py::test_rival_scouts_spawn_in_lair",
            "tests/world_build/test_orchestrator.py::test_leaders_live_and_halt_fires_with_real_scouts",
        ),
    ),
    Criterion(
        "C4",
        "Disguised-Priest rotation differs in identity and clues across two "
        "simulated resets (two-season-rotation scenario).",
        ("tests/disguised_priest/test_disguised_priest.py::test_two_season_rotation_full_cycle",),
    ),
    Criterion(
        "C5",
        "Henchmen hire / follow / fight / take treasure share / refuse below morale.",
        (
            "tests/henchmen/test_henchmen.py::test_successful_hire_joins_party",
            "tests/henchmen/test_henchmen.py::test_following_henchman_moves_with_employer",
            "tests/henchmen/test_henchmen.py::test_henchman_attacks_employer_target",
            "tests/henchmen/test_henchmen.py::test_half_xp_share_reduces_employer_gain",
            "tests/henchmen/test_henchmen.py::test_low_loyalty_refuses_suicidal_order",
        ),
    ),
    Criterion(
        "C6",
        "Default death (XP loss + retrievable corpse); hardcore death (delete + leaderboard).",
        (
            "tests/death/test_death.py::test_default_death_sets_xp_to_level_threshold",
            "tests/death/test_death.py::test_looting_corpse_restores_gear",
            "tests/death/test_death.py::test_hardcore_death_deletes_character",
            "tests/death/test_death.py::test_hardcore_death_appends_leaderboard_entry",
        ),
    ),
    Criterion(
        "C7",
        "Season reset clears world state but preserves character data "
        "(tests/seasonal_reset + world-build §13.9 rebuild persistence).",
        (
            "tests/seasonal_reset/test_seasonal_reset.py::test_reset_preserves_player_data",
            "tests/world_build/test_orchestrator.py::test_rebuild_world_repopulates_and_preserves_players",
        ),
    ),
    Criterion(
        "C8",
        "50 concurrent players, <100 ms command latency (the M16 C8 latency test).",
        ("tests/acceptance/test_latency_50.py::test_50_session_latency_under_budget",),
    ),
)

# Every proof node id across the whole table, paired with its owning criterion id.
_ALL_PROOFS: tuple[tuple[str, str], ...] = tuple(
    (c.id, node) for c in CRITERIA for node in c.proofs
)


def _split_node_id(node_id: str) -> tuple[Path, str]:
    """Split ``path::func`` into an absolute file path and the test function name."""
    rel_path, _, func = node_id.partition("::")
    assert func, f"node id {node_id!r} must be of the form '<path>::<test function>'"
    return REPO_ROOT / rel_path, func


@cache
def _module_test_functions(path: Path) -> frozenset[str]:
    """Module-level function names defined in ``path`` (AST — no import/boot)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return frozenset(
        node.name for node in tree.body if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    )


def test_all_eight_criteria_are_mapped() -> None:
    """The table covers exactly C1-C8 — no criterion is unmapped (§6.4)."""
    ids = [c.id for c in CRITERIA]
    assert ids == [f"C{n}" for n in range(1, 9)]
    # Every criterion names at least one proof.
    for c in CRITERIA:
        assert c.proofs, f"{c.id} has no proof test mapped"


@pytest.mark.parametrize(
    ("criterion_id", "node_id"),
    _ALL_PROOFS,
    ids=[f"{cid}:{node}" for cid, node in _ALL_PROOFS],
)
def test_proof_test_exists_and_is_collectable(criterion_id: str, node_id: str) -> None:
    """Each mapped proof test's file exists and defines the named test function.

    A renamed/removed proof fails here (§4.1) — the coverage claim cannot silently
    rot. The check is static (AST), so it does not boot the engine for the seven
    subsystem suites it references.
    """
    path, func = _split_node_id(node_id)
    assert path.is_file(), f"{criterion_id}: proof file missing — {path}"
    assert path.name.startswith("test_") and path.suffix == ".py", (
        f"{criterion_id}: proof {path} is not a pytest test module"
    )
    funcs = _module_test_functions(path)
    assert func in funcs, (
        f"{criterion_id}: proof test {func!r} not found in {path} "
        f"(renamed or removed?). Defined test functions: {sorted(funcs)}"
    )
    assert func.startswith("test_"), (
        f"{criterion_id}: proof {func!r} is not a collectable pytest function"
    )


def test_c8_proof_lives_in_this_acceptance_suite() -> None:
    """C8 is proven by the M16 latency test in this suite (acceptance.md §4.1)."""
    (c8,) = (c for c in CRITERIA if c.id == "C8")
    assert all("tests/acceptance/test_latency_50.py::" in node for node in c8.proofs)
