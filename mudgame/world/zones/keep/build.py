"""Thin ``build()`` hook for the Keep (zones spec R1 §2).

Delegates the heavy lifting to ``world.zones.builder`` and declares the one
Keep-specific fact: the Inner Bailey is the server-wide recall point
(CLAUDE.md §2). Idempotent — safe to run at first boot and on season reset.

The Evennia-backed builder is imported lazily inside ``build()`` so that merely
importing this module (and therefore the ``keep`` package) stays Evennia-free,
keeping the pure zone-data tests Django-free.
"""

from __future__ import annotations

from world.zones.keep.exits import EXITS
from world.zones.keep.npcs import NPCS, PLACEMENT, PRIEST_POOL
from world.zones.keep.rooms import ROOMS, ZONE


def build() -> None:
    """Create/update the Keep's rooms, exits, NPCs and mark the recall point."""
    from world.zones import builder  # noqa: PLC0415 (lazy: defer Evennia import)

    builder.build_zone(ZONE, ROOMS, EXITS)
    builder.tag_recall_point(ZONE, "inner_bailey")
    builder.build_npcs(ZONE, NPCS, PLACEMENT)
    builder.tag_priest_pool(ZONE, PRIEST_POOL)
