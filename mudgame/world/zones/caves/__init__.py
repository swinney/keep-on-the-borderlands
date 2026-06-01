"""The Caves of Chaos zone — the humanoid lairs (M9 kobold slice).

Exposes the standard zone interface. The data lists are pure (Evennia-free) and
importable for validation without booting the server; ``build`` is re-exported
from build.py, which defers its Evennia import until called, so importing this
package stays Evennia-free.
"""

from __future__ import annotations

from world.zones.caves.build import build
from world.zones.caves.exits import EXITS
from world.zones.caves.mobs import MOB_TEMPLATES
from world.zones.caves.npcs import NPCS
from world.zones.caves.rooms import ROOMS, ZONE
from world.zones.caves.spawns import SPAWNS

__all__ = ["EXITS", "MOB_TEMPLATES", "NPCS", "ROOMS", "SPAWNS", "ZONE", "build"]
