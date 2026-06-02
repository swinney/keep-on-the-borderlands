"""Shrine mob templates (zones spec docs/specs/zones/shrine.md §Mobs/factions).

The whole zone is faction ``cult`` (kind=``cult``, no parley): cult sentries
and acolytes hold the upper temple, undead haunt the crypts, spellcaster
adept-acolytes serve the leadership, and the Adept rules from the Inner Sanctum
as the standing endgame boss. The exposed-priest boss in ``boss_lair`` is a
separate M12 spawn that only appears after the disguised-priest plot triggers
global exposure, so it is *not* listed here.

The cult is not a leadership-halt tribe: it has no chief/shaman pair and no
designated rival, so killing the Adept never freezes repop. Instead the whole
zone restocks wholesale on the 24h reset cycle (spec §Systems wiring).

Ascending AC (architecture §5.1; asc = 19 - descending). ``faction`` id is the
exact id from ``world/factions/config.py``. OSE stat references in comments.

Pure data — no Evennia imports.
"""

from __future__ import annotations

from world.zones.records import MobRecord

MOB_TEMPLATES: list[MobRecord] = [
    # Cult sentry — armed temple guard. OSE Acolyte (1st-level cleric), mail +
    # shield: HD 1, AC 4 desc (15 asc), 1d6 weapon, morale 8.
    {
        "key": "cult_sentry",
        "name": "Cult Sentry",
        "faction": "cult",
        "level": 1,
        "hd": "1",
        "ac": 15,
        "attacks": "1d6 weapon",
        "morale": 8,
    },
    # Cult acolyte — fanatic rank-and-file. OSE Acolyte, leather: HD 1, AC 6
    # desc (13 asc), 1d6, morale 9 (zealotry steadies them).
    {
        "key": "cult_acolyte",
        "name": "Cult Acolyte",
        "faction": "cult",
        "level": 1,
        "hd": "1",
        "ac": 13,
        "attacks": "1d6 weapon",
        "morale": 9,
    },
    # Skeleton — mindless undead. OSE Skeleton: HD 1, AC 7 desc (12 asc), 1d6,
    # morale 12 (never breaks); turnable by clerics (R8).
    {
        "key": "shrine_skeleton",
        "name": "Skeleton",
        "faction": "cult",
        "level": 1,
        "hd": "1",
        "ac": 12,
        "attacks": "1d6 weapon",
        "morale": 12,
    },
    # Zombie — slow undead. OSE Zombie: HD 2, AC 8 desc (11 asc), 1d8, morale
    # 12; always acts last; turnable by clerics (R8).
    {
        "key": "shrine_zombie",
        "name": "Zombie",
        "faction": "cult",
        "level": 2,
        "hd": "2",
        "ac": 11,
        "attacks": "1d8 claw",
        "morale": 12,
    },
    # Wight — energy-draining undead. OSE Wight: HD 3, AC 5 desc (14 asc),
    # 1 level drain on hit, morale 12; hit only by silver/magic; turnable (R8).
    {
        "key": "shrine_wight",
        "name": "Wight",
        "faction": "cult",
        "level": 3,
        "hd": "3",
        "ac": 14,
        "attacks": "1d4 + energy drain",
        "morale": 12,
        "treasure": "grave-goods sealed in the reliquary",
    },
    # Adept-acolyte — cult spellcaster. OSE Acolyte (3rd-4th level cleric),
    # mail: HD 4, AC 4 desc (15 asc), 1d6, morale 10; casts hold/charm.
    {
        "key": "adept_acolyte",
        "name": "Adept-Acolyte",
        "faction": "cult",
        "level": 4,
        "hd": "4",
        "ac": 15,
        "attacks": "1d6 mace / cleric spells (hold, charm)",
        "morale": 10,
        "treasure": "spell components and a silver holy symbol of Chaos",
    },
    # The Adept — cult leader and standing endgame boss. An evil high priest:
    # plate + shield, HD 8, AC 2 desc (17 asc), 1d6+2 mace, morale 11; the full
    # cleric spell list. The strongest mob in the zone (test asserts this).
    {
        "key": "the_adept",
        "name": "the Adept",
        "faction": "cult",
        "level": 9,
        "hd": "8",
        "ac": 17,
        "attacks": "1d6+2 mace / cleric spells",
        "morale": 11,
        "treasure": "the Adept's regalia, ritual treasure, and the Shrine's keys",
    },
]
