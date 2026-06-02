"""Cave G — Gnolls + the Owlbear (caves spec docs/specs/zones/caves.md §Cave G).

The gnoll tribe (`gnoll`) occupies seven rooms in the southern ravine.  Hrrl
commands a war-band of vicious raiders locked in permanent conflict with the
goblin tribe (Cave D); killing either tribe's leaders triggers the rival to
scout the emptied lair (repop/config.py DESIGNATED_RIVAL).  Mange the shaman
keeps a shrine off the raider hall; a caged owlbear (``owlbear`` faction) is
chained in a side den off the throne room.

Exposes the standard tribe interface (pure data lists + ``build``); ``build``
defers its Evennia import via ``build_tribe`` so importing this package stays
Evennia-free.
"""

from __future__ import annotations

from world.zones.caves._tribe import build_tribe
from world.zones.caves.gnoll.exits import EXITS
from world.zones.caves.gnoll.mobs import MOB_TEMPLATES
from world.zones.caves.gnoll.npcs import NPCS, PLACEMENT
from world.zones.caves.gnoll.rooms import ROOMS
from world.zones.caves.gnoll.spawns import SPAWNS

__all__ = ["EXITS", "MOB_TEMPLATES", "NPCS", "PLACEMENT", "ROOMS", "SPAWNS", "build"]


def build() -> None:
    """Materialise the gnoll lair and register its spawns (idempotent)."""
    build_tribe(ROOMS, EXITS, SPAWNS, MOB_TEMPLATES, NPCS, PLACEMENT)
