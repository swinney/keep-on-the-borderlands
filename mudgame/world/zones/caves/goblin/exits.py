"""Goblin lair exits (zones spec docs/specs/zones/caves.md §Cave D).

Cave D (goblins) opens off the central scree via the northeast mouth, then
branches into wolf pens, the shaman's grotto, inner warrens, the chief's
throne, and the allied ogre's den.

Pure data — no Evennia import.
"""

from __future__ import annotations

from world.zones.caves._hub import expand
from world.zones.records import ExitRecord

# Bidirectional links: (from_key, direction_from, to_key). Cave D opens off
# the hub's central scree (ravine_mid) to the northeast.
_LINKS: list[tuple[str, str, str]] = [
    # entrance off the ravine's central scree
    ("ravine_mid", "ne", "goblin_mouth"),
    # the lair proper
    ("goblin_mouth", "n", "goblin_guard"),
    ("goblin_guard", "e", "goblin_pens"),
    ("goblin_guard", "n", "goblin_hall"),
    ("goblin_hall", "w", "goblin_grotto"),
    ("goblin_hall", "e", "goblin_warrens"),
    ("goblin_hall", "n", "goblin_throne"),
    ("goblin_throne", "e", "ogre_den"),
]

EXITS: list[ExitRecord] = expand(_LINKS)
