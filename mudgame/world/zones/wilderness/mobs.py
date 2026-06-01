"""Wilderness mob templates and wandering-encounter table.

Pure data — no Evennia imports. Factions ``beast``, ``bandit``, and ``lizard``
are minor factions added to ``world/factions/config.py`` for M8; they have no
Caves leadership/repop politics (wilderness spec §9).
"""

from __future__ import annotations

from world.zones.records import MobRecord

MOB_TEMPLATES: list[MobRecord] = [
    {
        "key": "giant_spider",
        "name": "Giant Spider",
        "faction": "beast",
        "level": 2,
        "hd": "2",
        "ac": 13,
        "attacks": "1d6 bite + poison save",
        "morale": 7,
    },
    {
        "key": "mountain_lion",
        "name": "Mountain Lion",
        "faction": "beast",
        "level": 3,
        "hd": "3+1",
        "ac": 13,
        "attacks": "1d6/1d6 claws + 1d8 bite",
        "morale": 8,
    },
    {
        "key": "brigand",
        "name": "Brigand",
        "faction": "bandit",
        "level": 1,
        "hd": "1",
        "ac": 12,
        "attacks": "1d6 weapon",
        "morale": 7,
        "treasure": "A",
    },
    {
        "key": "lizard_raider",
        "name": "Lizard Raider",
        "faction": "lizard",
        "level": 2,
        "hd": "2+1",
        "ac": 14,
        "attacks": "1d6 weapon",
        "morale": 8,
    },
    {
        "key": "skeleton",
        "name": "Skeleton",
        "faction": "cult",
        "level": 1,
        "hd": "1",
        "ac": 13,
        "attacks": "1d6 weapon",
        "morale": 12,
    },
]

# Weighted encounter table: (weight, mob_key). Higher weight = more frequent.
ENCOUNTER_TABLE: list[tuple[int, str]] = [
    (4, "brigand"),  # human raiders — most common wanderer
    (3, "mountain_lion"),  # predators in hills and roads
    (3, "giant_spider"),  # ambushers in the wooded area
    (2, "lizard_raider"),  # swamp territory
    (1, "skeleton"),  # rare cult undead patrol
]
