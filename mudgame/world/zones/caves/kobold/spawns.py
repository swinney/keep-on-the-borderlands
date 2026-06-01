"""Caves of Chaos spawn points — M9 kobold slice.

Feeds the repop manager (R3). Every tribe has exactly one ``chief`` and one
``shaman`` leader spawn (caves spec §systems): killing both within one window
halts the tribe's repop and triggers rival scouting. That *wiring* lands in the
next M9 task; this module is the static data it consumes.

Pure data — no Evennia imports.
"""

from __future__ import annotations

from world.zones.records import SpawnRecord

# Standard tribe respawn is 15 min (repop config STANDARD_RESPAWN); kept as a
# literal here to keep this data module dependency-free.
_STANDARD = 900

SPAWNS: list[SpawnRecord] = [
    # Cave mouth + guard post — sentries on watch.
    {"room": "kobold_mouth", "template": "kobold_sentry", "count": 2, "respawn_seconds": _STANDARD},
    {"room": "kobold_guard", "template": "kobold_sentry", "count": 2, "respawn_seconds": _STANDARD},
    # Kennels — the guard dog pack.
    {"room": "kobold_kennels", "template": "guard_dog", "count": 3, "respawn_seconds": _STANDARD},
    # The warren — the mass of the tribe.
    {
        "room": "kobold_warren",
        "template": "kobold_warrior",
        "count": 4,
        "respawn_seconds": _STANDARD,
    },
    # Shaman (leader) in his grotto.
    {
        "room": "kobold_grotto",
        "template": "kobold_shaman",
        "count": 1,
        "respawn_seconds": _STANDARD,
        "is_leader": True,
        "leader_role": "shaman",
    },
    # Chief (leader) in his den, with a warrior bodyguard.
    {
        "room": "kobold_den",
        "template": "kobold_chief",
        "count": 1,
        "respawn_seconds": _STANDARD,
        "is_leader": True,
        "leader_role": "chief",
    },
    {"room": "kobold_den", "template": "kobold_warrior", "count": 2, "respawn_seconds": _STANDARD},
]
