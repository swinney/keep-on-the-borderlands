"""Pure tests for the load-harness latency statistics (world-build spec §11).

``summarize`` reduces raw per-command latencies to a percentile summary; it is a
pure function (no Evennia), so these run Django-free — no DB fixture requested.
The engine-level ``run_load`` driving check lives in ``test_orchestrator.py``
(it needs a built world).
"""

from __future__ import annotations

from world.build import loadharness


def test_summarize_empty_is_all_zero() -> None:
    """A run that drove no commands yields a well-formed all-zero summary."""
    summary = loadharness.summarize([])

    assert summary.samples == 0
    assert summary.p50_ms == 0.0
    assert summary.p95_ms == 0.0
    assert summary.max_ms == 0.0


def test_summarize_percentiles_nearest_rank() -> None:
    """Nearest-rank percentiles and max over a known, unordered sample."""
    # 1..10 ms, shuffled; nearest-rank p50 -> rank ceil(.5*10)=5 -> 5.0,
    # p95 -> rank ceil(.95*10)=10 -> 10.0, max -> 10.0.
    samples = [5.0, 1.0, 9.0, 3.0, 7.0, 2.0, 8.0, 4.0, 10.0, 6.0]

    summary = loadharness.summarize(samples)

    assert summary.samples == 10
    assert summary.p50_ms == 5.0
    assert summary.p95_ms == 10.0
    assert summary.max_ms == 10.0


def test_summarize_single_sample() -> None:
    """One sample is its own p50, p95, and max."""
    summary = loadharness.summarize([42.0])

    assert summary.samples == 1
    assert summary.p50_ms == 42.0
    assert summary.p95_ms == 42.0
    assert summary.max_ms == 42.0
