"""Keep mob templates.

The Keep has no hostile mobs in v1 (the garrison repels intruders; PvP is
disabled). The list exists so the zone exposes the standard interface.
"""

from __future__ import annotations

from world.zones.records import MobRecord

MOB_TEMPLATES: list[MobRecord] = []
