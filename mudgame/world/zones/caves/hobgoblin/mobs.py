"""Hobgoblin lair mob templates (caves spec docs/specs/zones/caves.md §Cave E).

Ascending AC (architecture §5.1); ``faction`` id is the exact id from
``world/factions/config.py``. Hobgoblins are the most disciplined tribe: higher
AC and morale than kobolds or orcs, with a clear hierarchy from sentry to elite
guard to leader. Per the caves spec adaptation note, every tribe has both a
``chief`` and a ``shaman`` leader for uniform R3 leadership-halt behaviour —
here King Nardo and Vurt.

Pure data — no Evennia imports.
"""

from __future__ import annotations

from world.zones.records import MobRecord

MOB_TEMPLATES: list[MobRecord] = [
    {
        "key": "hobgoblin_sentry",
        "name": "Hobgoblin Sentry",
        "faction": "hobgoblin",
        "level": 2,
        "hd": "1+1",
        "ac": 14,
        "attacks": "1d8 weapon",
        "morale": 8,
    },
    {
        "key": "hobgoblin_soldier",
        "name": "Hobgoblin Soldier",
        "faction": "hobgoblin",
        "level": 2,
        "hd": "1+1",
        "ac": 14,
        "attacks": "1d8 weapon",
        "morale": 8,
    },
    {
        "key": "hobgoblin_elite",
        "name": "Hobgoblin Elite Guard",
        "faction": "hobgoblin",
        "level": 3,
        "hd": "2",
        "ac": 15,
        "attacks": "1d8 weapon",
        "morale": 9,
    },
    {
        "key": "hobgoblin_shaman",
        "name": "Vurt the Shaman",
        "faction": "hobgoblin",
        "level": 3,
        "hd": "2+1",
        "ac": 13,
        "attacks": "1d6 staff",
        "morale": 9,
        "treasure": "shaman's ritual goods",
        "is_leader": True,
        "leader_role": "shaman",
    },
    {
        "key": "hobgoblin_king",
        "name": "King Nardo",
        "faction": "hobgoblin",
        "level": 5,
        "hd": "5",
        "ac": 16,
        "attacks": "1d8+2 weapon",
        "morale": 10,
        "treasure": "Nardo's strongbox",
        "is_leader": True,
        "leader_role": "chief",
    },
]
