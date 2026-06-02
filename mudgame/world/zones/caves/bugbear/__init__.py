"""Cave F — the bugbear lair (zones spec docs/specs/zones/caves.md §Cave F).

A self-contained cave-tribe subpackage discovered at build time by
``caves.discovery``. Exposes the standard tribe interface (pure data lists +
a ``build``); ``build`` defers its Evennia import via ``build_tribe`` so
importing this package stays Evennia-free.
"""

from __future__ import annotations

from world.zones.caves._tribe import build_tribe
from world.zones.caves.bugbear.exits import EXITS
from world.zones.caves.bugbear.mobs import MOB_TEMPLATES
from world.zones.caves.bugbear.npcs import NPCS, PLACEMENT
from world.zones.caves.bugbear.rooms import ROOMS
from world.zones.caves.bugbear.spawns import SPAWNS

__all__ = ["EXITS", "MOB_TEMPLATES", "NPCS", "PLACEMENT", "ROOMS", "SPAWNS", "build"]


def build() -> None:
    """Materialise the bugbear lair and register its spawns (idempotent)."""
    build_tribe(ROOMS, EXITS, SPAWNS, MOB_TEMPLATES, NPCS, PLACEMENT)
