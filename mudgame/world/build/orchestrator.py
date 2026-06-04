"""Runtime boot orchestrator: build a populated world (world-build spec §4).

``build_all()`` is the single boot entry point (invoked from
``server/conf/at_initial_setup.py``). It brings the static zone content to life
in dependency order: ensure the four global managers exist, build every zone,
register the spawn points of zones whose ``build()`` does not self-register, then
run the initial population pass that materialises one live mob per registered
spawn point. It is **idempotent end to end** (spec §4, §7) — safe on every boot
and from the season rebuild — because every step it composes is idempotent: the
builder updates rooms/exits/NPCs in place, ``register_zone`` re-marks points
alive, and the spawner skips a point that already has a live instance.

Evennia is imported lazily inside the functions and the managers are referenced
by their dotted typeclass path (never imported as Python modules), so importing
this module stays Django-free and free of the ``managers -> build`` import cycle
(``repop_manager`` imports ``world.build.spawner`` at module load).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# (manager key, dotted typeclass path) — created if absent, fetched if present.
# Managers come up before any zone build so the cave tribes can self-register
# their spawns and the priest pool tagging lands against a live manager (§4.1).
_MANAGERS: tuple[tuple[str, str], ...] = (
    ("faction_manager", "world.managers.faction_manager.FactionManager"),
    ("repop_manager", "world.managers.repop_manager.RepopManager"),
    ("season_manager", "world.managers.season_manager.SeasonManager"),
    ("priest_manager", "world.managers.priest_manager.PriestManager"),
)


@dataclass(frozen=True)
class BuildSummary:
    """Counts of what the boot build produced — for the boot log and tests (§4)."""

    rooms: int
    exits: int
    npcs: int
    mobs: int


def _ensure_managers() -> dict[str, Any]:
    """Create the four global managers if absent, else fetch them by key (§4.1)."""
    from evennia.utils import create, search  # noqa: PLC0415

    managers: dict[str, Any] = {}
    for key, path in _MANAGERS:
        existing = search.search_script(key)
        managers[key] = existing[0] if existing else create.create_script(path)
    return managers


def build_all() -> BuildSummary:
    """Build + populate the whole world idempotently; return a count summary (§4).

    Zone build order matters (§4 step 2): the Keep first (recall point + priest
    pool), then the Wilderness (which wires the deferred Keep<->Wilderness gate
    once ``wilderness:keep_road`` is tagged), then the Caves (each tribe
    self-registers its spawns against the now-present ``repop_manager``), then the
    Shrine. The Cave of the Unknown is a sealed v1 stub (CLAUDE.md §2) with no
    zone package, so it is not built.
    """
    from evennia.utils.search import search_object_by_tag  # noqa: PLC0415

    from world.zones import caves, keep, shrine, wilderness  # noqa: PLC0415
    from world.zones.builder import (  # noqa: PLC0415
        EXIT_CATEGORY,
        NPC_CATEGORY,
        ROOM_CATEGORY,
        build_exits,
    )

    managers = _ensure_managers()
    repop = managers["repop_manager"]

    keep.build()
    wilderness.build()
    caves.build()
    shrine.build()

    # Settle the one inter-zone exit deferred by build order: the Caves minotaur
    # maze descends to the Shrine (caves:minotaur_shrine_passage -> shrine_gate),
    # but the Caves build above ran before the Shrine rooms existed, so that
    # forward exit was skipped. Re-running the Caves exits now (idempotent) wires
    # it — the same "later zone settles the deferred link" pattern the Wilderness
    # build uses to complete the Keep<->Wilderness gate.
    build_exits("caves", caves.EXITS)

    # Register the spawn points of zones whose build() does not self-register
    # (§4 step 3): the Wilderness set-pieces and the Shrine cult. The Keep ships
    # no faction spawns (empty SPAWNS) but is registered uniformly for clarity;
    # re-registering is idempotent (register marks each point alive).
    repop.register_zone("keep", keep.SPAWNS, keep.MOB_TEMPLATES)
    repop.register_zone("wilderness", wilderness.SPAWNS, wilderness.MOB_TEMPLATES)
    repop.register_zone("shrine", shrine.SPAWNS, shrine.MOB_TEMPLATES)

    # Initial population pass (§4 step 4): one live mob per registered spawn
    # point, including every tribe's chief/shaman leaders so the M6 halt has
    # real targets. The spawner is idempotent, so a re-boot adds no duplicates.
    mobs = repop.populate()

    return BuildSummary(
        rooms=len(search_object_by_tag(category=ROOM_CATEGORY)),
        exits=len(search_object_by_tag(category=EXIT_CATEGORY)),
        npcs=len(search_object_by_tag(category=NPC_CATEGORY)),
        mobs=mobs,
    )
