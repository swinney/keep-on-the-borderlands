"""Wilderness set-piece spawn points for the repop manager.

Pure data — no Evennia imports. No leadership halts in the wilderness
(wilderness spec §10): no spawn carries a ``leader_role``.
"""

from __future__ import annotations

from world.zones.records import SpawnRecord

SPAWNS: list[SpawnRecord] = [
    # Woods — giant spider population
    {"room": "woods_west", "template": "giant_spider", "count": 2, "respawn_seconds": 900},
    {"room": "woods_deep", "template": "giant_spider", "count": 3, "respawn_seconds": 900},
    # Hills — mountain lion territory
    {"room": "hills_low", "template": "mountain_lion", "count": 2, "respawn_seconds": 900},
    {"room": "hills_high", "template": "mountain_lion", "count": 1, "respawn_seconds": 900},
    # Hermit's pet (set-piece companion)
    {"room": "hermit_hut", "template": "mountain_lion", "count": 1, "respawn_seconds": 900},
    # Raider camp — brigand garrison
    {"room": "raider_camp", "template": "brigand", "count": 3, "respawn_seconds": 1800},
    # Swamp — lizard folk patrol
    {"room": "swamp", "template": "lizard_raider", "count": 2, "respawn_seconds": 900},
    # Ruined tower — cult skeleton patrol
    {"room": "old_tower", "template": "skeleton", "count": 2, "respawn_seconds": 900},
]
