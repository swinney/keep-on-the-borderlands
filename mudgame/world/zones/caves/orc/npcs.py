"""Orc static NPCs — Cave B (Vile Rune) and Cave C (Decapitator).

The captured Keep soldier in orc_dec_prison is a quest hook wired in the M13
quest task (R9). The empty lists keep the standard tribe interface uniform.

Pure data — no Evennia imports.
"""

from __future__ import annotations

from world.zones.records import NpcRecord

NPCS: list[NpcRecord] = []

PLACEMENT: dict[str, str] = {}
