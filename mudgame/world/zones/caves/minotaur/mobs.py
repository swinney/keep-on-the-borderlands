"""Minotaur mob template — Cave H (the Minotaur's Maze).

The minotaur is a solitary beast (``minotaur`` faction, kind=``solitary``).
It is *not* a repop tribe; there are no chief or shaman leader spawns — the R3
leadership-halt mechanic does not apply.  Killing it simply schedules the
standard 15-min respawn.

OSE stat reference:
  Minotaur — HD 6, AC 6 descending (13 ascending), attacks: gore 1d6 + bite
  1d6 (or weapon 2d6 instead of gore), morale 12 (fights to the death; beast).

Pure data — no Evennia imports.
"""

from __future__ import annotations

from world.zones.records import MobRecord

MOB_TEMPLATES: list[MobRecord] = [
    {
        "key": "cave_h_minotaur",
        "name": "the Minotaur",
        "faction": "minotaur",
        "level": 6,
        "hd": "6",
        "ac": 13,
        "attacks": "1d6 gore / 1d6 bite",
        "morale": 12,
        "treasure": "accumulated hoard of coin, weapons, and gems",
    },
]
