"""Gnoll mob templates — Cave G (Hrrl's gnolls + the Owlbear).

Ascending AC (architecture §5.1); ``faction`` ids from ``world/factions/config.py``.
Gnolls are powerful raiders: tall, hyena-headed, and merciless.  They are at
war with the goblins (Cave D) and maintain a caged owlbear as a guard-beast.

OSE stat references:
  Gnoll    — HD 2, AC 5 descending (14 ascending), attack 2d4, morale 8.
  Hyena    — HD 2+2, AC 7 descending (12 ascending), attack 2d4 bite, morale 9.
  Owlbear  — HD 5, AC 5 descending (14 ascending), attack 1d8/1d8/1d6
             (claw/claw/beak), morale 12 (always fights; beast).

Chief Hrrl (HD 4) wears captured chain and fights with a great flail.  Mange
the shaman (HD 3) calls upon dark powers and fights with a bone-tipped staff.

Per the caves spec adaptation note both the chief and shaman are leader spawns
so the R3 leadership-halt fires when both are down.

The owlbear (``owlbear`` faction) is an independent beast, not a gnoll tribe
leader.  Killing it shifts ``owlbear`` faction standing, not ``gnoll``.

Pure data — no Evennia imports.
"""

from __future__ import annotations

from world.zones.records import MobRecord

MOB_TEMPLATES: list[MobRecord] = [
    # ── Gnoll tribe ───────────────────────────────────────────────────────
    {
        "key": "gnoll_raider",
        "name": "Gnoll Raider",
        "faction": "gnoll",
        "level": 2,
        "hd": "2",
        "ac": 14,
        "attacks": "2d4 weapon",
        "morale": 8,
    },
    {
        "key": "gnoll_hyena",
        "name": "Gnoll Hyena",
        "faction": "gnoll",
        "level": 2,
        "hd": "2+2",
        "ac": 12,
        "attacks": "2d4 bite",
        "morale": 9,
    },
    {
        "key": "gnoll_shaman",
        "name": "Mange the Shaman",
        "faction": "gnoll",
        "level": 3,
        "hd": "3",
        "ac": 12,
        "attacks": "1d6 staff",
        "morale": 9,
        "treasure": "bone-fetish satchel and ritual components",
        "is_leader": True,
        "leader_role": "shaman",
    },
    {
        "key": "gnoll_chief",
        "name": "Hrrl the Chief",
        "faction": "gnoll",
        "level": 4,
        "hd": "4",
        "ac": 15,
        "attacks": "2d4+1 great flail",
        "morale": 11,
        "treasure": "iron strongbox of raided loot",
        "is_leader": True,
        "leader_role": "chief",
    },
    # ── Owlbear (`owlbear` faction, caged beast) ──────────────────────────
    {
        "key": "cave_g_owlbear",
        "name": "the Owlbear",
        "faction": "owlbear",
        "level": 5,
        "hd": "5",
        "ac": 14,
        "attacks": "1d8/1d8/1d6 claw/claw/beak",
        "morale": 12,
        "treasure": "gem cache buried beneath its den",
    },
]
