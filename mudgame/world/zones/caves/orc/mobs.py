"""Orc mob templates — Cave B (Vile Rune, `orc_vol`) and Cave C (Decapitator, `orc_dec`).

Ascending AC (architecture §5.1); ``faction`` ids from ``world/factions/config.py``.
Orcs are a mid-tier tribe: stronger than kobolds, organised, and disciplined.
OSE stat references: HD 1+1, AC 6 (ascending 13), attack 1d6; chiefs are HD 4.

Per the caves spec adaptation note both tribes have a chief and a shaman leader
spawn so the R3 leadership-halt is uniform across all tribes.

The orc_vol ↔ orc_dec rivalry is encoded in factions/config.py (tension +24,
war band) and repop/config.py (designated rivals of each other) — no additional
mob-level data is needed to wire the rivalry.

Pure data — no Evennia imports.
"""

from __future__ import annotations

from world.zones.records import MobRecord

MOB_TEMPLATES: list[MobRecord] = [
    # ── Orcs of the Vile Rune (orc_vol) ─────────────────────────────────
    {
        "key": "orc_vol_warrior",
        "name": "Vile Rune Warrior",
        "faction": "orc_vol",
        "level": 1,
        "hd": "1+1",
        "ac": 13,
        "attacks": "1d6 weapon",
        "morale": 8,
    },
    {
        "key": "orc_vol_war_party",
        "name": "Vile Rune War-Party Orc",
        "faction": "orc_vol",
        "level": 1,
        "hd": "1+1",
        "ac": 13,
        "attacks": "1d6 weapon",
        "morale": 9,
    },
    {
        "key": "orc_vol_shaman",
        "name": "Mawg the Shaman",
        "faction": "orc_vol",
        "level": 2,
        "hd": "2",
        "ac": 13,
        "attacks": "1d6 weapon",
        "morale": 9,
        "treasure": "ritual fetishes and red-dyed coin",
        "is_leader": True,
        "leader_role": "shaman",
    },
    {
        "key": "orc_vol_chief",
        "name": "Grukk the Chief",
        "faction": "orc_vol",
        "level": 3,
        "hd": "3",
        "ac": 14,
        "attacks": "1d8 weapon",
        "morale": 9,
        "treasure": "chief's iron chest",
        "is_leader": True,
        "leader_role": "chief",
    },
    # ── Orcs of the Decapitator (orc_dec) ────────────────────────────────
    {
        "key": "orc_dec_warrior",
        "name": "Decapitator Warrior",
        "faction": "orc_dec",
        "level": 1,
        "hd": "1+1",
        "ac": 13,
        "attacks": "1d6 weapon",
        "morale": 8,
    },
    {
        "key": "orc_dec_totem_guard",
        "name": "Totem Guard",
        "faction": "orc_dec",
        "level": 2,
        "hd": "2",
        "ac": 14,
        "attacks": "1d6+1 weapon",
        "morale": 9,
    },
    {
        "key": "orc_dec_shaman",
        "name": "Ssruk the Shaman",
        "faction": "orc_dec",
        "level": 2,
        "hd": "2",
        "ac": 13,
        "attacks": "1d6 weapon",
        "morale": 9,
        "treasure": "bone carvings and ritual chalk",
        "is_leader": True,
        "leader_role": "shaman",
    },
    {
        "key": "orc_dec_chief",
        "name": "Bloodtusk the Chief",
        "faction": "orc_dec",
        "level": 3,
        "hd": "3",
        "ac": 15,
        "attacks": "1d8 weapon",
        "morale": 10,
        "treasure": "scattered plunder",
        "is_leader": True,
        "leader_role": "chief",
    },
]
