"""Minotaur spawn point — Cave H (the Minotaur's Maze).

Single unique spawn in the maze heart.  The minotaur is a solitary beast, not
a tribe; there are no chief or shaman leader spawns, so the R3 leadership-halt
mechanic never fires for this faction (DESIGNATED_RIVAL["minotaur"] is None).

Pure data — no Evennia imports.
"""

from __future__ import annotations

from world.zones.records import SpawnRecord

_STANDARD = 900  # 15 min (repop config STANDARD_RESPAWN)

SPAWNS: list[SpawnRecord] = [
    {
        "room": "minotaur_heart",
        "template": "cave_h_minotaur",
        "count": 1,
        "respawn_seconds": _STANDARD,
    },
]
