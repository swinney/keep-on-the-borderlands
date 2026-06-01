"""Bugbear lair spawn points (caves spec §Cave F).

Feeds the repop manager (R3). One ``chief`` (Grosh) and one ``shaman`` (Hrak)
are leader spawns; killing both within one 15-min window halts the tribe 60 min
and triggers the designated rival (hobgoblin) to scout the empty lair
(repop config DESIGNATED_RIVAL[\"bugbear\"] == \"hobgoblin\").

Pure data — no Evennia imports.
"""

from __future__ import annotations

from world.zones.records import SpawnRecord

_STANDARD = 900  # 15 min; mirrors repop config STANDARD_RESPAWN

SPAWNS: list[SpawnRecord] = [
    # Cave mouth — guards at the entrance.
    {
        "room": "bugbear_mouth",
        "template": "bugbear_guard",
        "count": 2,
        "respawn_seconds": _STANDARD,
    },
    # Ambush passage — lurking maulers.
    {
        "room": "bugbear_passage",
        "template": "bugbear_mauler",
        "count": 2,
        "respawn_seconds": _STANDARD,
    },
    # Barracks — the bulk of the tribe.
    {
        "room": "bugbear_barracks",
        "template": "bugbear_mauler",
        "count": 4,
        "respawn_seconds": _STANDARD,
    },
    # Prisoner's cell — guard posted to watch the captive.
    {"room": "bugbear_hold", "template": "bugbear_guard", "count": 1, "respawn_seconds": _STANDARD},
    # Shaman (leader) in his den.
    {
        "room": "bugbear_shaman",
        "template": "bugbear_shaman",
        "count": 1,
        "respawn_seconds": _STANDARD,
        "is_leader": True,
        "leader_role": "shaman",
    },
    # Chief (leader) in his lair, with elite bodyguards.
    {
        "room": "bugbear_chief",
        "template": "bugbear_chief",
        "count": 1,
        "respawn_seconds": _STANDARD,
        "is_leader": True,
        "leader_role": "chief",
    },
    {
        "room": "bugbear_chief",
        "template": "bugbear_mauler",
        "count": 2,
        "respawn_seconds": _STANDARD,
    },
]
