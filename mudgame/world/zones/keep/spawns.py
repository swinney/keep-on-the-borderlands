"""Keep spawn points.

None: the Keep has no hostile mobs (see mobs.py). Static service/quest NPCs are
placed by ``build()`` from npcs.py, not via the repop manager.
"""

from __future__ import annotations

from world.zones.records import SpawnRecord

SPAWNS: list[SpawnRecord] = []
