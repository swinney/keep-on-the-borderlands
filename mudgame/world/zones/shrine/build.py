"""Thin ``build()`` hook for the Shrine (zones spec R1 §2).

Delegates to ``world.zones.builder``. The Shrine is no recall point and ships
no static NPCs in v1, so the hook only builds rooms and exits. The inter-zone
exit back to the Caves minotaur maze wires itself once both zones exist
(builder skips unresolved targets). Idempotent — safe at first boot and on the
24h season reset.

The Evennia-backed builder is imported lazily inside ``build()`` so that merely
importing this module (and the ``shrine`` package) stays Evennia-free, keeping
the pure zone-data tests Django-free.
"""

from __future__ import annotations

from world.zones.shrine.exits import EXITS
from world.zones.shrine.rooms import ROOMS, ZONE


def build() -> None:
    """Create/update the Shrine's rooms and exits (idempotent)."""
    from world.zones import builder  # noqa: PLC0415 (lazy: defer Evennia import)

    builder.build_zone(ZONE, ROOMS, EXITS)
