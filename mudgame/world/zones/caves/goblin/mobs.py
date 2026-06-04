"""Goblin lair mob templates (caves spec §Cave D).

Ascending AC (architecture §5.1); ``faction`` ids match ``world/factions/config.py``.
Goblins are a mid-tier tribe: stronger than kobolds, weaker than hobgoblins.
Per the caves spec adaptation note every tribe is granted both a ``chief`` and
a ``shaman`` leader — here Snagg and Yeek — so the R3 leadership-halt is
uniform. The ogre is an allied combatant with its own ``ogre`` faction.

Pure data — no Evennia imports.
"""

from __future__ import annotations

from world.zones.records import MobRecord

MOB_TEMPLATES: list[MobRecord] = [
    {
        "key": "goblin_warrior",
        "name": "Goblin Warrior",
        "faction": "goblin",
        "level": 1,
        "hd": "1-1",
        "ac": 13,
        "attacks": "1d6 weapon",
        "morale": 7,
    },
    {
        "key": "goblin_wolf",
        "name": "Goblin Wolf",
        "faction": "goblin",
        "level": 2,
        "hd": "2+2",
        "ac": 14,
        "attacks": "1d6 bite",
        "morale": 8,
    },
    {
        "key": "goblin_shaman",
        "name": "Yeek the Shaman",
        "faction": "goblin",
        "level": 3,
        "hd": "3",
        "ac": 13,
        "attacks": "1d6 weapon",
        "morale": 9,
        "treasure": "shaman fetishes",
        "is_leader": True,
        "leader_role": "shaman",
    },
    {
        "key": "goblin_chief",
        "name": "Snagg the Chief",
        "faction": "goblin",
        "level": 3,
        "hd": "3",
        "ac": 14,
        "attacks": "1d8 weapon",
        "morale": 9,
        "treasure": "chief's treasure hoard",
        "is_leader": True,
        "leader_role": "chief",
        "giver_key": "goblin_chief",
    },
    {
        "key": "ogre",
        "name": "The Ogre",
        "faction": "ogre",
        "level": 4,
        "hd": "4+1",
        "ac": 15,
        "attacks": "1d10 club",
        "morale": 10,
        "treasure": "ogre's plundered hoard",
    },
]
