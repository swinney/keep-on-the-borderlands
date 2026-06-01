"""Bugbear lair exits (zones spec docs/specs/zones/caves.md §Cave F).

Cave F opens off the ravine's south ledge (northeast entrance). Intra-lair
connectivity is declared as bidirectional links and expanded to directed exits
via the shared hub helper.

Pure data — no Evennia import.
"""

from __future__ import annotations

from world.zones.caves._hub import expand
from world.zones.records import ExitRecord

# Bidirectional links: (from_key, direction_from, to_key). Cave F opens off the
# hub's south ledge and runs north to the chief's lair.
_LINKS: list[tuple[str, str, str]] = [
    # entrance off the ravine's south ledge
    ("ravine_south", "ne", "bugbear_mouth"),
    # the lair proper
    ("bugbear_mouth", "n", "bugbear_passage"),
    ("bugbear_passage", "n", "bugbear_barracks"),
    ("bugbear_barracks", "e", "bugbear_hold"),
    ("bugbear_barracks", "w", "bugbear_treasury"),
    ("bugbear_barracks", "n", "bugbear_shaman"),
    ("bugbear_shaman", "e", "bugbear_chief"),
]

EXITS: list[ExitRecord] = expand(_LINKS)
