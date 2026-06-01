"""Thin ``build()`` hook for the Caves of Chaos (zones spec R1 §2).

The caves are built in two phases: the shared ravine hub (``_hub``) first — it
owns the ravine spine and the inter-zone link back to the Wilderness — then
every cave-tribe subpackage discovered under ``caves/`` (``discovery``). Adding a
tribe is therefore drop-in: create ``caves/<tribe>/`` exposing a ``build`` and it
is materialised automatically, with no edit here.

Idempotent (each phase delegates to idempotent builders). Evennia is imported
lazily — via the hub/tribe build paths — so importing this module stays
Evennia-free for the pure-data test suites.
"""

from __future__ import annotations


def build() -> None:
    """Build the ravine hub, then every discovered cave tribe (idempotent)."""
    from world.zones.caves import _hub, discovery  # noqa: PLC0415 (lazy)

    _hub.build()
    for tribe in discovery.tribes():
        tribe.build()
