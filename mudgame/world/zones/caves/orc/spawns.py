"""Orc spawn points — Cave B (orc_vol) and Cave C (orc_dec).

Feeds the repop manager (R3). Each tribe has exactly one chief and one shaman
leader spawn (caves spec §systems); killing both within one 15-min window halts
that tribe's repop for 60 min and triggers the designated rival to scout.

Designated rivals (repop/config.py DESIGNATED_RIVAL):
  orc_vol -> orc_dec   (Decapitators move into the empty Vile Rune lair)
  orc_dec -> orc_vol   (Vile Rune move into the empty Decapitator lair)

Pure data — no Evennia imports.
"""

from __future__ import annotations

from world.zones.records import SpawnRecord

_STANDARD = 900  # 15 min (repop config STANDARD_RESPAWN)

SPAWNS: list[SpawnRecord] = [
    # ── Cave B — Vile Rune (orc_vol) ────────────────────────────────────
    # Entrance sentries.
    {
        "room": "orc_vol_mouth",
        "template": "orc_vol_warrior",
        "count": 2,
        "respawn_seconds": _STANDARD,
    },
    # Guard room.
    {
        "room": "orc_vol_guard",
        "template": "orc_vol_warrior",
        "count": 2,
        "respawn_seconds": _STANDARD,
    },
    # Barracks — the bulk of the warriors.
    {
        "room": "orc_vol_barracks",
        "template": "orc_vol_warrior",
        "count": 4,
        "respawn_seconds": _STANDARD,
    },
    # Inner warrens — warriors guarding the vulnerable.
    {
        "room": "orc_vol_warrens",
        "template": "orc_vol_warrior",
        "count": 3,
        "respawn_seconds": _STANDARD,
    },
    # Shaman (leader) in his den.
    {
        "room": "orc_vol_shaman",
        "template": "orc_vol_shaman",
        "count": 1,
        "respawn_seconds": _STANDARD,
        "is_leader": True,
        "leader_role": "shaman",
    },
    # War council — the war party, ready for raids.
    {
        "room": "orc_vol_war_room",
        "template": "orc_vol_war_party",
        "count": 3,
        "respawn_seconds": _STANDARD,
    },
    # Chief (leader) in his chamber with bodyguards.
    {
        "room": "orc_vol_chief",
        "template": "orc_vol_chief",
        "count": 1,
        "respawn_seconds": _STANDARD,
        "is_leader": True,
        "leader_role": "chief",
    },
    {
        "room": "orc_vol_chief",
        "template": "orc_vol_warrior",
        "count": 2,
        "respawn_seconds": _STANDARD,
    },
    # ── Cave C — Decapitator (orc_dec) ──────────────────────────────────
    # Entrance sentries.
    {
        "room": "orc_dec_mouth",
        "template": "orc_dec_warrior",
        "count": 2,
        "respawn_seconds": _STANDARD,
    },
    # Guard chamber.
    {
        "room": "orc_dec_guard",
        "template": "orc_dec_warrior",
        "count": 2,
        "respawn_seconds": _STANDARD,
    },
    # Warriors' hall — the main fighting force.
    {
        "room": "orc_dec_hall",
        "template": "orc_dec_warrior",
        "count": 4,
        "respawn_seconds": _STANDARD,
    },
    # Totem chamber — elite guards.
    {
        "room": "orc_dec_totem",
        "template": "orc_dec_totem_guard",
        "count": 2,
        "respawn_seconds": _STANDARD,
    },
    # Shaman (leader) in his den.
    {
        "room": "orc_dec_shaman",
        "template": "orc_dec_shaman",
        "count": 1,
        "respawn_seconds": _STANDARD,
        "is_leader": True,
        "leader_role": "shaman",
    },
    # Prison — one guard watching the captive.
    {
        "room": "orc_dec_prison",
        "template": "orc_dec_warrior",
        "count": 1,
        "respawn_seconds": _STANDARD,
    },
    # Chief (leader) in his den with bodyguards.
    {
        "room": "orc_dec_chief",
        "template": "orc_dec_chief",
        "count": 1,
        "respawn_seconds": _STANDARD,
        "is_leader": True,
        "leader_role": "chief",
    },
    {
        "room": "orc_dec_chief",
        "template": "orc_dec_warrior",
        "count": 2,
        "respawn_seconds": _STANDARD,
    },
]
