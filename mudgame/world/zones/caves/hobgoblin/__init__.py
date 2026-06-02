"""Cave E — the hobgoblin lair (zones spec docs/specs/zones/caves.md §Cave E).

A self-contained cave-tribe subpackage discovered at build time by
``caves.discovery``. Exposes the standard tribe interface (pure data lists +
a ``build``); ``build`` defers its Evennia import via ``build_tribe`` so
importing this package stays Evennia-free.
"""

from __future__ import annotations

from world.zones.caves._tribe import build_tribe
from world.zones.caves.hobgoblin.exits import EXITS
from world.zones.caves.hobgoblin.mobs import MOB_TEMPLATES
from world.zones.caves.hobgoblin.npcs import NPCS, PLACEMENT
from world.zones.caves.hobgoblin.rooms import ROOMS
from world.zones.caves.hobgoblin.spawns import SPAWNS

__all__ = ["EXITS", "MOB_TEMPLATES", "NPCS", "PLACEMENT", "ROOMS", "SPAWNS", "build"]


def build() -> None:
    """Materialise the hobgoblin lair and register its spawns (idempotent)."""
    build_tribe(ROOMS, EXITS, SPAWNS, MOB_TEMPLATES, NPCS, PLACEMENT)
