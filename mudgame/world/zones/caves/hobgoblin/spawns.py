"""Hobgoblin lair spawn points (caves spec docs/specs/zones/caves.md §Cave E).

Feeds the repop manager (R3). Every tribe has exactly one ``chief`` and one
``shaman`` leader spawn: killing both within one window halts this tribe's
repop for 60 min and triggers the designated rival's scouting party (repop
spec §3-4). The hobgoblins are disciplined - more troops than most tribes,
concentrated at choke points and around the leaders.

Pure data — no Evennia imports.
"""

from __future__ import annotations

from world.zones.records import SpawnRecord

_STANDARD = 900  # 15 min, matches repop config STANDARD_RESPAWN

SPAWNS: list[SpawnRecord] = [
    # Gate — two sentries hold the cave mouth.
    {
        "room": "hobgoblin_gate",
        "template": "hobgoblin_sentry",
        "count": 2,
        "respawn_seconds": _STANDARD,
    },
    # Entry hall — two soldiers on duty.
    {
        "room": "hobgoblin_hall",
        "template": "hobgoblin_soldier",
        "count": 2,
        "respawn_seconds": _STANDARD,
    },
    # Barracks — four soldiers, most of the tribe's fighting strength.
    {
        "room": "hobgoblin_barracks",
        "template": "hobgoblin_soldier",
        "count": 4,
        "respawn_seconds": _STANDARD,
    },
    # Mess — two off-duty soldiers.
    {
        "room": "hobgoblin_mess",
        "template": "hobgoblin_soldier",
        "count": 2,
        "respawn_seconds": _STANDARD,
    },
    # Inner passage — two soldiers patrolling the rear corridors.
    {
        "room": "hobgoblin_inner",
        "template": "hobgoblin_soldier",
        "count": 2,
        "respawn_seconds": _STANDARD,
    },
    # Armory — one soldier on inventory guard.
    {
        "room": "hobgoblin_armory",
        "template": "hobgoblin_soldier",
        "count": 1,
        "respawn_seconds": _STANDARD,
    },
    # Vurt's chamber (shaman leader) + one elite bodyguard.
    {
        "room": "hobgoblin_shaman",
        "template": "hobgoblin_shaman",
        "count": 1,
        "respawn_seconds": _STANDARD,
        "is_leader": True,
        "leader_role": "shaman",
    },
    {
        "room": "hobgoblin_shaman",
        "template": "hobgoblin_elite",
        "count": 1,
        "respawn_seconds": _STANDARD,
    },
    # Guard room — three elite guards before the throne.
    {
        "room": "hobgoblin_guard",
        "template": "hobgoblin_elite",
        "count": 3,
        "respawn_seconds": _STANDARD,
    },
    # King Nardo's throne room (chief leader) + two elite bodyguards.
    {
        "room": "hobgoblin_throne",
        "template": "hobgoblin_king",
        "count": 1,
        "respawn_seconds": _STANDARD,
        "is_leader": True,
        "leader_role": "chief",
    },
    {
        "room": "hobgoblin_throne",
        "template": "hobgoblin_elite",
        "count": 2,
        "respawn_seconds": _STANDARD,
    },
]
