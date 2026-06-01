"""The Caves of Chaos zone — the humanoid lairs (fanout-harness.md §3).

The zone is the shared ravine hub (``_hub``) plus every cave-tribe subpackage
discovered under ``caves/`` (``discovery``). This package re-exports the standard
zone interface; the data lists are *aggregates* of the hub data and every
discovered tribe's data, so validation suites that import ``caves.ROOMS`` (etc.)
see the whole zone. All data is pure (Evennia-free); ``build`` defers its Evennia
import until called, so importing this package stays Evennia-free.
"""

from __future__ import annotations

from typing import Any

from world.zones.caves import _hub, discovery
from world.zones.caves.build import build

ZONE = _hub.ZONE


def _aggregate(attr: str, tribes: list[Any]) -> list[Any]:
    """Concatenate the hub's ``HUB_<attr>`` with every tribe's ``<attr>``."""
    out: list[Any] = list(getattr(_hub, f"HUB_{attr}", []))
    for tribe in tribes:
        out.extend(getattr(tribe, attr, []))
    return out


_discovered = discovery.tribes()
ROOMS = _aggregate("ROOMS", _discovered)
EXITS = _aggregate("EXITS", _discovered)
MOB_TEMPLATES = _aggregate("MOB_TEMPLATES", _discovered)
SPAWNS = _aggregate("SPAWNS", _discovered)
NPCS = _aggregate("NPCS", _discovered)

__all__ = ["EXITS", "MOB_TEMPLATES", "NPCS", "ROOMS", "SPAWNS", "ZONE", "build"]
