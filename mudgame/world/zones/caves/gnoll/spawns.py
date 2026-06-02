"""Gnoll spawn points — Cave G (gnoll tribe + the Owlbear).

Feeds the repop manager (R3).  The gnoll tribe has exactly one chief (Hrrl)
and one shaman (Mange) as leader spawns; killing both within one 15-min window
halts gnoll repop for 60 min and triggers the designated rival (goblin) to
scout (repop/config.py DESIGNATED_RIVAL: gnoll -> goblin).

The owlbear (``cave_g_owlbear``, ``owlbear`` faction) is a single unique spawn
in the owlbear's den.  It is *not* a gnoll leader; its death triggers ``owlbear``
faction standing shifts, not the gnoll leadership halt.

Pure data — no Evennia imports.
"""

from __future__ import annotations

from world.zones.records import SpawnRecord

_STANDARD = 900  # 15 min (repop config STANDARD_RESPAWN)

SPAWNS: list[SpawnRecord] = [
    # ── Gnoll tribe ───────────────────────────────────────────────────────
    # Cave mouth sentries.
    {
        "room": "gnoll_mouth",
        "template": "gnoll_raider",
        "count": 2,
        "respawn_seconds": _STANDARD,
    },
    # Entry passage — tunnel guards.
    {
        "room": "gnoll_entry",
        "template": "gnoll_raider",
        "count": 2,
        "respawn_seconds": _STANDARD,
    },
    # Raider hall — main war-band.
    {
        "room": "gnoll_raider_hall",
        "template": "gnoll_raider",
        "count": 4,
        "respawn_seconds": _STANDARD,
    },
    # Hyena pit — the pack.
    {
        "room": "gnoll_hyena_pit",
        "template": "gnoll_hyena",
        "count": 3,
        "respawn_seconds": _STANDARD,
    },
    # Mange's den — shaman (leader).
    {
        "room": "gnoll_shaman",
        "template": "gnoll_shaman",
        "count": 1,
        "respawn_seconds": _STANDARD,
        "is_leader": True,
        "leader_role": "shaman",
    },
    # Hrrl's throne room — chief (leader) + bodyguards.
    {
        "room": "gnoll_chief",
        "template": "gnoll_chief",
        "count": 1,
        "respawn_seconds": _STANDARD,
        "is_leader": True,
        "leader_role": "chief",
    },
    {
        "room": "gnoll_chief",
        "template": "gnoll_raider",
        "count": 2,
        "respawn_seconds": _STANDARD,
    },
    # ── Owlbear ───────────────────────────────────────────────────────────
    # Single unique spawn; not a gnoll leader.
    {
        "room": "gnoll_owlbear_den",
        "template": "cave_g_owlbear",
        "count": 1,
        "respawn_seconds": _STANDARD,
    },
]
