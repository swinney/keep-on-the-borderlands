"""Kobold lair exits (zones spec docs/specs/zones/caves.md §Cave A).

Intra-tribe connectivity is declared once as bidirectional links and expanded
to directed ``EXITS`` (both ways) via the shared hub helper. The entrance link
(ravine_north → kobold_mouth) lives here because it is the tribe attaching
itself to the hub's north ledge; the builder resolves ``ravine_north`` by tag,
so the hub need not know about it.

Pure data — no Evennia import.
"""

from __future__ import annotations

from world.zones.caves._hub import expand
from world.zones.records import ExitRecord

# Bidirectional links: (from_key, direction_from, to_key). Cave A opens off the
# hub's north ledge and runs inward to the chief's den.
_LINKS: list[tuple[str, str, str]] = [
    # entrance off the ravine's north ledge
    ("ravine_north", "nw", "kobold_mouth"),
    # the lair proper
    ("kobold_mouth", "n", "kobold_guard"),
    ("kobold_guard", "e", "kobold_kennels"),
    ("kobold_guard", "n", "kobold_warren"),
    ("kobold_warren", "w", "kobold_grotto"),
    ("kobold_warren", "n", "kobold_den"),
]

EXITS: list[ExitRecord] = expand(_LINKS)
