"""Goblin lair static NPCs (caves spec §Cave D).

No static service or quest NPCs in this slice; the ogre's bribe quest hook
is wired in the M13 quest task. Empty lists keep the zone interface uniform.

Pure data — no Evennia imports.
"""

from __future__ import annotations

from world.zones.records import NpcRecord

NPCS: list[NpcRecord] = []

# NPC key -> room key it stands in (consumed by builder.build_npcs).
PLACEMENT: dict[str, str] = {}
