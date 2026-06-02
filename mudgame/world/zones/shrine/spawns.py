"""Shrine spawn points (zones spec docs/specs/zones/shrine.md).

The cult repopulates wholesale on the 24h reset cycle rather than the standard
15-min tribe respawn. Populated in the M11 mobs slice; the empty list keeps the
zone's standard interface intact for the pure-data layout tests.

Pure data — no Evennia import.
"""

from __future__ import annotations

from world.zones.records import SpawnRecord

SPAWNS: list[SpawnRecord] = []
