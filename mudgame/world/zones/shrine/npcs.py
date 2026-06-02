"""Shrine static NPCs (zones spec docs/specs/zones/shrine.md).

The Shrine's inhabitants are hostile cult mobs (see mobs.py), not static
service NPCs, so this list is empty in v1. It exists so the zone exposes the
standard interface; ``PLACEMENT`` maps any future NPC key to its room key.

Pure data — no Evennia import.
"""

from __future__ import annotations

from world.zones.records import NpcRecord

NPCS: list[NpcRecord] = []

# NPC key -> room key. Empty while the Shrine ships no static NPCs.
PLACEMENT: dict[str, str] = {}
