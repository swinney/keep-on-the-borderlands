"""Caves of Chaos static NPCs — M9 kobold slice.

The kobold lair has no static service/quest NPCs in this slice; the captive in
the chief's den is a quest hook wired in the M9 quest task (R9). The empty lists
keep the zone's standard interface uniform with the other zones.

Pure data — no Evennia imports.
"""

from __future__ import annotations

from world.zones.records import NpcRecord

NPCS: list[NpcRecord] = []

# NPC key -> room key it stands in (consumed by builder.build_npcs).
PLACEMENT: dict[str, str] = {}
