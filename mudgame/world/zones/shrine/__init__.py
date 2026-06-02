"""The Shrine zone — the endgame temple of the Cult of Evil Chaos.

Exposes the standard zone interface. The data lists are pure (Evennia-free) and
importable for validation without booting the server; ``build`` is re-exported
from build.py, which defers its Evennia import until called, so importing this
package stays Evennia-free.
"""

from __future__ import annotations

from world.zones.shrine.build import build
from world.zones.shrine.exits import EXITS
from world.zones.shrine.mobs import MOB_TEMPLATES
from world.zones.shrine.npcs import NPCS
from world.zones.shrine.rooms import ROOMS, ZONE
from world.zones.shrine.spawns import SPAWNS

__all__ = ["EXITS", "MOB_TEMPLATES", "NPCS", "ROOMS", "SPAWNS", "ZONE", "build"]
