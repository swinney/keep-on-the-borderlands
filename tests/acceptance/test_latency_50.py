"""Criterion C8 — 50-player <100 ms command latency (acceptance.md §2, §6.1).

Drives the M15 load harness (``world.build.loadharness.run_load``) at 50 sessions
against ``build_all()``'s fully-populated world and asserts both that the run was
**honest and complete** (``recall_built``, requested-vs-driven, full command
count) and that the per-command latency lands under named budgets that sit with
margin beneath the 100 ms criterion.

**What this measures, and what it does not (honesty — acceptance.md §2.3, §5):**
this is single-process, **server-side per-command** latency — the time the engine
spends in the cmdhandler (``Object.execute_cmd``) for one command, timed by the
harness with ``perf_counter`` (ADR 0005, the in-process transport). The 50
sessions are driven sequentially in one process, **not** over 50 simultaneous
sockets, so this is *not* a wire-level concurrent measurement; that telnet driver
is the documented ADR-0005 fallback and is deferred. What the criterion's word
"concurrent" buys here is that **50 players' worth of populated-world state is
resident** — every zone, every spawned mob/leader, all four managers — while each
command is processed, so each sample pays the real cost of resolving against a
fully-populated world rather than a bare grid.

**Budget provenance (acceptance.md §2.4):** the budgets below were set from an
observed baseline of ``run_load(50)`` against the populated world — p95 ≈ 3.7 ms,
max ≈ 5.0 ms over two runs. They sit far under the 100 ms criterion with generous
headroom (~13x p95, ~18x max) so the test asserts the criterion is met with margin
and tolerates CI-machine noise, rather than pinning a brittle exact figure. If a
future run's observed p95 were *not* under 100 ms the criterion would be UNMET —
that is a finding to escalate via ``docs/questions.md``, never a budget to weaken
(CLAUDE.md §3).
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from world.build import loadharness, orchestrator

# Honesty/completeness constants for the 50-session run.
SESSIONS = 50

# Latency budgets (ms), both under the 100 ms C8 criterion with margin (§2.4).
# Observed baseline against the populated world: p95 ≈ 3.7 ms, max ≈ 5.0 ms.
P95_BUDGET_MS = 50.0
MAX_BUDGET_MS = 90.0


@pytest.fixture
def built_world() -> Iterator[orchestrator.BuildSummary]:
    """Build the full populated world once; yield the summary; tear it down.

    The teardown mirrors ``tests/world_build/test_orchestrator``'s grid-safe
    sequence (the world includes the xyzgrid Wilderness), reused here so the
    acceptance suite leaves no rooms/mobs/managers behind.
    """
    from tests.world_build.test_orchestrator import _teardown_world  # noqa: PLC0415

    summary = orchestrator.build_all()
    try:
        yield summary
    finally:
        _teardown_world()


@pytest.mark.django_db
def test_50_session_latency_under_budget(built_world: orchestrator.BuildSummary) -> None:
    """50 sessions through the populated world: honest report + per-command latency.

    The world the load runs against is the one ``built_world`` populated, so the
    latency is paid against realistic state (asserted populated below).
    """
    summary = built_world
    # The load runs against a genuinely populated world, not a bare grid (§2.3).
    assert summary.rooms > 0
    assert summary.mobs > 0

    # build=False: reuse the already-built world from the fixture (do not rebuild).
    report = loadharness.run_load(SESSIONS, build=False)

    # ── honesty + completeness (§2.2 step 2): a partial/unbuilt world fails loud ──
    assert report.recall_built is True
    assert report.requested_sessions == SESSIONS
    assert report.driven_sessions == SESSIONS
    assert report.commands_run == SESSIONS * len(loadharness.DEFAULT_COMMAND_MIX)
    assert report.latency.samples == report.commands_run

    # ── the C8 latency target, with margin under the 100 ms criterion (§2.2/§2.4) ──
    assert report.latency.p95_ms < P95_BUDGET_MS
    assert report.latency.max_ms < MAX_BUDGET_MS
    # And — the criterion itself, stated explicitly — comfortably under 100 ms.
    assert report.latency.p95_ms < 100.0


def test_budgets_are_under_the_100ms_criterion() -> None:
    """The named budgets sit under the C8 100 ms criterion (reviewable in one place)."""
    assert P95_BUDGET_MS < 100.0
    assert MAX_BUDGET_MS < 100.0
