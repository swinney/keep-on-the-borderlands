"""Shrine mob templates (zones spec docs/specs/zones/shrine.md).

The whole zone is faction ``cult``: sentries and acolytes, undead in the
crypts, spellcaster adept-acolytes, the Adept boss, and the exposed-priest
boss. Populated in the M11 mobs slice; the list exists now so the zone exposes
the standard interface for the pure-data layout tests.

Pure data — no Evennia import.
"""

from __future__ import annotations

from world.zones.records import MobRecord

MOB_TEMPLATES: list[MobRecord] = []
