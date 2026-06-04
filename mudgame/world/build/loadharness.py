"""Load-harness sketch for the M14 50-player <100 ms latency criterion (spec §11).

M15 ships the *populated, bootable target* plus this harness sketch; the actual
50-player <100 ms **measurement** is the M14 task that consumes it. The harness
builds the world, connects N synthetic player characters to the recall point,
drives a representative command mix against the real command set while timing
each command server-side, and **reports the population it actually drove** — it
never silently caps the load it was asked for (spec §11).

Transport (decided in this slice, ADR 0005): in-process synthetic characters
driven through ``Object.execute_cmd`` — the same full cmdhandler path the engine
runs for a real session — rather than an external telnet driver. It runs inside
the test process alongside ``build_all()``, needs no live portal/network, and
yields direct server-side per-command timing, which is exactly the quantity the
M14 criterion measures. An external telnet driver is kept as a documented
fallback for a true end-to-end network measurement (ADR 0005 "Considered").

The latency *statistics* are a pure function (``summarize``), unit-testable
Django-free; only the session driving (``run_load``) imports Evennia, and it does
so lazily so importing this module stays Django-free (spec §3 discipline).
"""

from __future__ import annotations

import math
import time
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from world.build import orchestrator

CHARACTER_TYPECLASS = "typeclasses.characters.PlayerCharacter"

# A representative read/move/combat command mix (spec §11: "connect, move,
# attack, and cast"). ``look``/``score`` always resolve; the movement and combat
# verbs are best-effort against whatever stands in the recall room, so the
# harness never depends on fragile world geometry — a command that finds no
# exit/target still contributes a timed sample (the work the server did to
# reject it). Callers measuring a specific scenario pass their own sequence.
DEFAULT_COMMAND_MIX: tuple[str, ...] = ("look", "score", "north", "look", "south")


@dataclass(frozen=True)
class LatencySummary:
    """Percentile summary of per-command server-side latencies (spec §11)."""

    samples: int
    p50_ms: float
    p95_ms: float
    max_ms: float


@dataclass(frozen=True)
class LoadReport:
    """What a load run actually drove — requested vs driven, never silently capped.

    ``recall_built`` is ``False`` when the world has no recall room to connect
    synthetic players to (an unbuilt or partial build): the harness then drives
    nothing and reports ``driven_sessions == 0`` rather than spawning location-less
    loadbots and falsely claiming it served the requested load (spec §11 "report,
    not silently cap").
    """

    requested_sessions: int
    driven_sessions: int
    commands_run: int
    latency: LatencySummary
    recall_built: bool = True


def _percentile(ordered: Sequence[float], pct: float) -> float:
    """Nearest-rank percentile of an already-sorted sample (pure helper)."""
    if not ordered:
        return 0.0
    rank = max(1, math.ceil(pct / 100.0 * len(ordered)))
    return ordered[min(rank, len(ordered)) - 1]


def summarize(latencies_ms: Sequence[float]) -> LatencySummary:
    """Reduce raw per-command latencies (ms) to a percentile summary (pure; spec §11).

    Empty input yields an all-zero summary rather than raising, so a run that
    drove no commands still produces a well-formed report.
    """
    if not latencies_ms:
        return LatencySummary(samples=0, p50_ms=0.0, p95_ms=0.0, max_ms=0.0)
    ordered = sorted(latencies_ms)
    return LatencySummary(
        samples=len(ordered),
        p50_ms=_percentile(ordered, 50.0),
        p95_ms=_percentile(ordered, 95.0),
        max_ms=ordered[-1],
    )


def run_load(
    requested_sessions: int,
    *,
    commands: Sequence[str] = DEFAULT_COMMAND_MIX,
    build: bool = True,
) -> LoadReport:
    """Drive ``requested_sessions`` synthetic players and report the load (spec §11).

    Builds (or assumes, with ``build=False``) a populated world, spawns one
    synthetic ``PlayerCharacter`` per requested session at the recall point, runs
    each through ``commands`` while timing every command with ``perf_counter``,
    then tears the synthetic characters down. The returned ``LoadReport`` records
    both the requested and the **actually driven** session count plus the latency
    summary — the harness reports the population it drove and never silently caps
    it. The 50-player <100 ms assertion itself is the M14 task that calls this.

    A command that raises (no such exit/target for a synthetic bot in an empty
    room) is swallowed *after* its latency is recorded: a sketch harness must not
    abort the whole run on one rejected command, and the rejection's cost is
    legitimate server-side work to sample.
    """
    from evennia.utils import create, logger  # noqa: PLC0415
    from evennia.utils.search import search_object_by_tag  # noqa: PLC0415

    if build:
        orchestrator.build_all()

    recall_matches = search_object_by_tag("inner_bailey")
    room = recall_matches[0] if recall_matches else None
    if room is None:
        # No recall point means the world is unbuilt or only partially built;
        # location-less loadbots would measure nothing yet read as a full run.
        # Surface the failed build honestly instead of silently capping (spec §11).
        logger.log_err(
            "loadharness: no recall room ('inner_bailey') — world unbuilt; driving 0 sessions"
        )
        return LoadReport(
            requested_sessions=requested_sessions,
            driven_sessions=0,
            commands_run=0,
            latency=summarize([]),
            recall_built=False,
        )

    latencies_ms: list[float] = []
    driven = 0
    commands_run = 0
    characters: list[Any] = []
    try:
        for index in range(requested_sessions):
            char = create.create_object(CHARACTER_TYPECLASS, key=f"loadbot-{index}", location=room)
            characters.append(char)
            driven += 1
            for command in commands:
                start = time.perf_counter()
                try:
                    char.execute_cmd(command)
                except Exception:
                    # A sketch must not abort the whole run on one rejected
                    # command (no such exit/target for a bot in an empty room).
                    logger.log_trace(f"loadharness: command {command!r} raised; sample kept")
                latencies_ms.append((time.perf_counter() - start) * 1000.0)
                commands_run += 1
    finally:
        for char in characters:
            if char.pk is not None:
                char.delete()

    return LoadReport(
        requested_sessions=requested_sessions,
        driven_sessions=driven,
        commands_run=commands_run,
        latency=summarize(latencies_ms),
    )
