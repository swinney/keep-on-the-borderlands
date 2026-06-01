"""Caves of Chaos mob templates — M9 kobold slice (caves spec §Cave A).

Ascending AC (architecture §5.1); ``faction`` ids are the exact ids from
``world/factions/config.py``. The kobolds are the weakest tribe: low HD, AC, and
morale. Per the caves spec adaptation note every tribe is granted both a
``chief`` and a ``shaman`` leader so the R3 leadership-halt is uniform and
testable — here Sharptooth and Grik.

Pure data — no Evennia imports.
"""

from __future__ import annotations

from world.zones.records import MobRecord

MOB_TEMPLATES: list[MobRecord] = [
    {
        "key": "kobold_sentry",
        "name": "Kobold Sentry",
        "faction": "kobold",
        "level": 1,
        "hd": "1d4",
        "ac": 12,
        "attacks": "1d4 weapon",
        "morale": 6,
    },
    {
        "key": "kobold_warrior",
        "name": "Kobold Warrior",
        "faction": "kobold",
        "level": 1,
        "hd": "1d4",
        "ac": 12,
        "attacks": "1d4 weapon",
        "morale": 6,
    },
    {
        "key": "guard_dog",
        "name": "Guard Dog",
        "faction": "kobold",
        "level": 1,
        "hd": "1+1",
        "ac": 12,
        "attacks": "1d4 bite",
        "morale": 7,
    },
    {
        "key": "kobold_shaman",
        "name": "Grik the Shaman",
        "faction": "kobold",
        "level": 2,
        "hd": "2",
        "ac": 12,
        "attacks": "1d4 weapon",
        "morale": 8,
        "treasure": "kobold charms",
        "is_leader": True,
        "leader_role": "shaman",
    },
    {
        "key": "kobold_chief",
        "name": "Sharptooth the Chief",
        "faction": "kobold",
        "level": 2,
        "hd": "1+1",
        "ac": 13,
        "attacks": "1d6 weapon",
        "morale": 8,
        "treasure": "chief's coin hoard",
        "is_leader": True,
        "leader_role": "chief",
    },
]
