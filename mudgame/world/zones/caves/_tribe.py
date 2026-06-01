"""Shared build helper for cave-tribe subpackages (zones spec R1 §2).

Each tribe under ``caves/`` is a self-contained subpackage exposing its own
rooms/exits/mobs/spawns/NPCs. They all materialise the same way: build the
rooms+exits, place any static NPCs, then register the tribe's spawns with the
repop manager. This helper centralises that sequence so a tribe's ``build()`` is
a one-liner.

Evennia is imported lazily inside :func:`build_tribe`, so importing this module
stays Evennia-free for the pure-data test suites.
"""

from __future__ import annotations

from world.zones.caves._hub import ZONE
from world.zones.records import ExitRecord, MobRecord, NpcRecord, RoomRecord, SpawnRecord


def build_tribe(
    rooms: list[RoomRecord],
    exits: list[ExitRecord],
    spawns: list[SpawnRecord],
    mob_templates: list[MobRecord],
    npcs: list[NpcRecord] | None = None,
    placement: dict[str, str] | None = None,
) -> None:
    """Build one cave tribe: rooms+exits, static NPCs, then repop spawns.

    Idempotent (delegates to the idempotent builder). The repop registration is
    skipped silently if the manager is not yet running, mirroring the deferred
    inter-zone wiring in the hub build.
    """
    from evennia.utils.search import search_script  # noqa: PLC0415

    from world.zones import builder  # noqa: PLC0415 (lazy: defer Evennia import)

    builder.build_zone(ZONE, rooms, exits)
    if npcs:
        builder.build_npcs(ZONE, npcs, placement or {})

    managers = search_script("repop_manager")
    if managers:
        managers[0].register_zone(ZONE, spawns, mob_templates)
