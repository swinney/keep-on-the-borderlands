"""Shrine spawn points (zones spec docs/specs/zones/shrine.md §Mobs/factions).

The cult does not repopulate on the standard 15-min tribe cadence; the whole
zone restocks wholesale on the 24h reset cycle (spec §Systems wiring, R3). Every
spawn therefore pins ``respawn_seconds`` to the Shrine-reset interval and carries
no ``is_leader`` flag — the cult has no chief/shaman pair, so the leadership-halt
mechanic never applies. The Adept is a boss, not a repop leader.

``boss_lair`` is intentionally empty: the exposed-priest boss spawns there only
after the M12 disguised-priest plot triggers global exposure. The altar room,
secret vault, river cavern, and cells hold objects/quest content, not mobs.

Pure data — no Evennia imports.
"""

from __future__ import annotations

from world.zones.records import SpawnRecord

_RESET = 24 * 60 * 60  # 24h, matches repop config SHRINE_RESET

SPAWNS: list[SpawnRecord] = [
    # Narthex — sentries by the warning bell.
    {"room": "narthex", "template": "cult_sentry", "count": 2, "respawn_seconds": _RESET},
    # Nave — acolyte patrols among the bone pews.
    {"room": "nave_evil", "template": "cult_acolyte", "count": 3, "respawn_seconds": _RESET},
    # Side chapels — one acolyte tending each.
    {"room": "side_chapel_n", "template": "cult_acolyte", "count": 1, "respawn_seconds": _RESET},
    {"room": "side_chapel_s", "template": "cult_acolyte", "count": 1, "respawn_seconds": _RESET},
    # Upper crypt — risen skeletons and shambling zombies.
    {"room": "crypt_upper", "template": "shrine_skeleton", "count": 3, "respawn_seconds": _RESET},
    {"room": "crypt_upper", "template": "shrine_zombie", "count": 2, "respawn_seconds": _RESET},
    # Lower crypt — wights warding the sealed reliquary.
    {"room": "crypt_lower", "template": "shrine_wight", "count": 2, "respawn_seconds": _RESET},
    # Acolyte dormitory — resting acolytes and two spellcasters.
    {"room": "acolyte_dorm", "template": "cult_acolyte", "count": 2, "respawn_seconds": _RESET},
    {"room": "acolyte_dorm", "template": "adept_acolyte", "count": 2, "respawn_seconds": _RESET},
    # Adept's study — a spellcaster attendant guarding the lore.
    {"room": "adept_study", "template": "adept_acolyte", "count": 1, "respawn_seconds": _RESET},
    # Hall of Ritual — set-piece ambush: acolytes plus a caster in the galleries.
    {"room": "ritual_hall", "template": "cult_acolyte", "count": 2, "respawn_seconds": _RESET},
    {"room": "ritual_hall", "template": "adept_acolyte", "count": 1, "respawn_seconds": _RESET},
    # Inner Sanctum — the Adept boss with a pair of sentry bodyguards.
    {"room": "inner_sanctum", "template": "the_adept", "count": 1, "respawn_seconds": _RESET},
    {"room": "inner_sanctum", "template": "cult_sentry", "count": 2, "respawn_seconds": _RESET},
]
