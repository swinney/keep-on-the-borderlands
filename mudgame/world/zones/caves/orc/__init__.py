"""Cave B + C -- the two orc tribes (zones spec docs/specs/zones/caves.md §Cave B-C).

The Vile Rune (orc_vol) and the Decapitators (orc_dec) are a single content unit:
the two tribes are blood enemies (tension +24, war band) and designated repop
rivals of each other. Splitting them across separate clones would create a
cross-package dependency, so both lairs live here.

Exposes the standard tribe interface (pure data lists + ``build``); ``build``
defers its Evennia import via ``build_tribe`` so importing this package stays
Evennia-free.
"""

from __future__ import annotations

from world.zones.caves._tribe import build_tribe
from world.zones.caves.orc.exits import EXITS
from world.zones.caves.orc.mobs import MOB_TEMPLATES
from world.zones.caves.orc.npcs import NPCS, PLACEMENT
from world.zones.caves.orc.rooms import ROOMS
from world.zones.caves.orc.spawns import SPAWNS

__all__ = ["EXITS", "MOB_TEMPLATES", "NPCS", "PLACEMENT", "ROOMS", "SPAWNS", "build"]


def build() -> None:
    """Materialise both orc lairs and register their spawns (idempotent)."""
    build_tribe(ROOMS, EXITS, SPAWNS, MOB_TEMPLATES, NPCS, PLACEMENT)
