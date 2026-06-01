"""Goblin lair spawn points (caves spec §Cave D).

Feeds the repop manager (R3). Every tribe has exactly one ``chief`` and one
``shaman`` leader spawn (caves spec §systems): killing both within one window
halts the tribe's repop for 60 minutes and triggers the designated rival
(``gnoll``, per repop config) to send a scouting party into the empty lair.

The ogre is an allied combatant in a separate faction (``ogre``) and has no
``is_leader`` flag — it is not part of the goblin tribe's leadership halt.

Pure data — no Evennia imports.
"""

from __future__ import annotations

from world.zones.records import SpawnRecord

_STANDARD = 900  # 15 min standard respawn (repop config STANDARD_RESPAWN)

SPAWNS: list[SpawnRecord] = [
    # Entrance and guard post — warriors on watch.
    {
        "room": "goblin_mouth",
        "template": "goblin_warrior",
        "count": 2,
        "respawn_seconds": _STANDARD,
    },
    {
        "room": "goblin_guard",
        "template": "goblin_warrior",
        "count": 2,
        "respawn_seconds": _STANDARD,
    },
    # Wolf pens — the pack of goblin mounts.
    {"room": "goblin_pens", "template": "goblin_wolf", "count": 3, "respawn_seconds": _STANDARD},
    # Main hall — the bulk of the tribe.
    {"room": "goblin_hall", "template": "goblin_warrior", "count": 5, "respawn_seconds": _STANDARD},
    # Inner warrens — overflow warriors.
    {
        "room": "goblin_warrens",
        "template": "goblin_warrior",
        "count": 3,
        "respawn_seconds": _STANDARD,
    },
    # Shaman (leader) in the grotto.
    {
        "room": "goblin_grotto",
        "template": "goblin_shaman",
        "count": 1,
        "respawn_seconds": _STANDARD,
        "is_leader": True,
        "leader_role": "shaman",
    },
    # Chief (leader) on his throne, with bodyguards.
    {
        "room": "goblin_throne",
        "template": "goblin_chief",
        "count": 1,
        "respawn_seconds": _STANDARD,
        "is_leader": True,
        "leader_role": "chief",
    },
    {
        "room": "goblin_throne",
        "template": "goblin_warrior",
        "count": 2,
        "respawn_seconds": _STANDARD,
    },
    # The ogre in its side den — allied but independent faction.
    {"room": "ogre_den", "template": "ogre", "count": 1, "respawn_seconds": _STANDARD},
]
