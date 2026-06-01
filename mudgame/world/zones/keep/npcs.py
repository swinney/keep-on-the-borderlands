"""Keep static NPCs (shops, services, quest givers).

Placeholder for this milestone slice: the rooms-and-exits task wires the Keep's
geography and recall point only. The provisioner/armorer/weaponsmith/trader,
bank, tavern roster, chapel staff, and quest givers are populated by the later
M7 tasks (shops + economy, tavern/chapel integration). The empty list keeps the
zone's standard interface intact until then.
"""

from __future__ import annotations

from world.zones.records import NpcRecord

NPCS: list[NpcRecord] = []
