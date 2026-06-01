"""Bugbear lair mob templates (caves spec §Cave F).

Ascending AC (architecture §5.1); ``faction`` ids match ``world/factions/config.py``.
Bugbears are powerful ambush hunters: high HD, good AC, and strong melee. Per
the caves spec adaptation note every tribe has both a ``chief`` and a ``shaman``
leader so the R3 leadership-halt is uniform — here Grosh and Hrak.

Pure data — no Evennia imports.
"""

from __future__ import annotations

from world.zones.records import MobRecord

MOB_TEMPLATES: list[MobRecord] = [
    {
        "key": "bugbear_mauler",
        "name": "Bugbear Mauler",
        "faction": "bugbear",
        "level": 3,
        "hd": "3+1",
        "ac": 14,
        "attacks": "1d8 weapon",
        "morale": 9,
    },
    {
        "key": "bugbear_guard",
        "name": "Bugbear Guard",
        "faction": "bugbear",
        "level": 3,
        "hd": "3+1",
        "ac": 14,
        "attacks": "1d8 weapon",
        "morale": 9,
    },
    {
        "key": "bugbear_shaman",
        "name": "Hrak the Shaman",
        "faction": "bugbear",
        "level": 4,
        "hd": "4",
        "ac": 14,
        "attacks": "1d6 club",
        "morale": 10,
        "treasure": "shaman's fetish-bundle",
        "is_leader": True,
        "leader_role": "shaman",
    },
    {
        "key": "bugbear_chief",
        "name": "Grosh the Chief",
        "faction": "bugbear",
        "level": 5,
        "hd": "4+1",
        "ac": 15,
        "attacks": "1d8+1 greatclub",
        "morale": 10,
        "treasure": "chief's plundered hoard",
        "is_leader": True,
        "leader_role": "chief",
    },
]
