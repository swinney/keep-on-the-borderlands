"""Hobgoblin lair static NPCs (caves spec docs/specs/zones/caves.md §Cave E).

The captive in the inner quarters is a quest hook wired in the quest task (R9).
The empty lists keep the standard tribe interface uniform with other zones.

Pure data — no Evennia imports.
"""

from __future__ import annotations

from world.zones.records import NpcRecord

NPCS: list[NpcRecord] = []

# NPC key -> room key it stands in (consumed by builder.build_npcs).
PLACEMENT: dict[str, str] = {}
