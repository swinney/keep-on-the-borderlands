"""Cave H — The Minotaur's Maze (caves spec docs/specs/zones/caves.md §Cave H).

A solitary minotaur (``minotaur`` faction) occupies a small labyrinth cut into
the southern rock beneath the ravine.  The beast is not a repop tribe — it has
no chief or shaman — so the R3 leadership-halt mechanic does not apply here.
Killing the minotaur simply schedules its standard respawn.  A deep passage at
the maze's far end leads onward to the Shrine of Evil Chaos (``shrine:shrine_gate``).

Exposes the standard tribe interface (pure data lists + ``build``); ``build``
defers its Evennia import via ``build_tribe`` so importing this package stays
Evennia-free.
"""

from __future__ import annotations

from world.zones.caves._tribe import build_tribe
from world.zones.caves.minotaur.exits import EXITS
from world.zones.caves.minotaur.mobs import MOB_TEMPLATES
from world.zones.caves.minotaur.npcs import NPCS, PLACEMENT
from world.zones.caves.minotaur.rooms import ROOMS
from world.zones.caves.minotaur.spawns import SPAWNS

__all__ = ["EXITS", "MOB_TEMPLATES", "NPCS", "PLACEMENT", "ROOMS", "SPAWNS", "build"]


def build() -> None:
    """Materialise the minotaur maze and register its spawn (idempotent)."""
    build_tribe(ROOMS, EXITS, SPAWNS, MOB_TEMPLATES, NPCS, PLACEMENT)
