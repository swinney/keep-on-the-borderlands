"""The Wilderness zone — overland hex map between the Keep and the Caves.

Exposes the standard zone interface plus the xyzgrid-specific XYMAP_DATA and
ENCOUNTER_TABLE. The data lists are pure (Evennia-free) and importable for
validation without booting the server; ``build`` defers its Evennia imports
until called.

Unlike the Keep, this zone has no ROOMS or EXITS lists — the xyzgrid contrib
owns room and exit creation from XYMAP_DATA. See wilderness.md §1.
"""

from __future__ import annotations

from world.zones.wilderness.build import build
from world.zones.wilderness.mobs import ENCOUNTER_TABLE, MOB_TEMPLATES
from world.zones.wilderness.npcs import NPCS, PLACEMENT
from world.zones.wilderness.spawns import SPAWNS
from world.zones.wilderness.xymap import XYMAP_DATA

__all__ = [
    "ENCOUNTER_TABLE",
    "MOB_TEMPLATES",
    "NPCS",
    "PLACEMENT",
    "SPAWNS",
    "XYMAP_DATA",
    "build",
]
