"""Bugbear lair static NPCs (caves spec §Cave F).

The captive merchant in ``bugbear_hold`` is a quest hook wired in the M13
quest task (R9). The empty lists keep the zone interface uniform.

Pure data — no Evennia imports.
"""

from __future__ import annotations

from world.zones.records import NpcRecord

NPCS: list[NpcRecord] = []

# NPC key -> room key it stands in (consumed by builder.build_npcs).
PLACEMENT: dict[str, str] = {}
