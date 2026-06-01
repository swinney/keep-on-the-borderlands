"""Thin ``build()`` hook for the Caves of Chaos (zones spec R1 §2).

Delegates room/exit creation to ``world.zones.builder`` and then completes the
inter-zone link to the Wilderness. Build order is keep → wilderness → caves
(mirroring the existing keep↔wilderness chain), so when the caves are built the
Wilderness already exists but its ``ravine_mouth → caves`` exit was deferred
(the caves rooms did not yet exist). This hook therefore:

* tags the ravine floor with the ``caves:ravine_mouth`` identity the Wilderness
  exit (wilderness spec §exits) resolves against — the caves spec keys the hub
  room ``ravine`` ("The Ravine Floor"), so the tag is an alias reconciling the
  two specs without touching the Wilderness zone; and
* creates the forward ``enter`` exit from the Wilderness ravine mouth into the
  caves, idempotently (shared exit identity), so a second build — or a build in
  either order — never duplicates it.

Idempotent. Evennia is imported lazily so importing this module stays
Evennia-free for the pure-data test suites.
"""

from __future__ import annotations

from world.zones.caves.exits import EXITS
from world.zones.caves.mobs import MOB_TEMPLATES
from world.zones.caves.rooms import ROOMS, ZONE
from world.zones.caves.spawns import SPAWNS

# Stable identity of the ravine-mouth crossing, shared with the Wilderness zone
# so whichever zone builds last finds and reuses the existing exit.
_ENTER_EXIT_ID = "wilderness:ravine_mouth:enter"
_RAVINE_MOUTH_ALIAS = "caves:ravine_mouth"


def build() -> None:
    """Create/update the caves' rooms and exits and link them to the Wilderness."""
    from world.zones import builder  # noqa: PLC0415 (lazy: defer Evennia import)

    builder.build_zone(ZONE, ROOMS, EXITS)
    _link_to_wilderness()
    _register_spawns()


def _register_spawns() -> None:
    """Register the kobold tribe's spawn points with the repop manager (R3 §1).

    Wires the chief + shaman leaders into the leadership-halt + rival-scouting
    machinery (repop.md §3-4). Skips silently if the manager is not yet running,
    mirroring the deferred inter-zone wiring above.
    """
    from evennia.utils.search import search_script  # noqa: PLC0415

    managers = search_script("repop_manager")
    if managers:
        managers[0].register_zone(ZONE, SPAWNS, MOB_TEMPLATES)


def _link_to_wilderness() -> None:
    """Tag the ravine mouth and wire the Wilderness → caves forward exit."""
    from evennia.utils import create  # noqa: PLC0415
    from evennia.utils.search import search_object_by_tag  # noqa: PLC0415

    from world.zones.builder import EXIT_CATEGORY, ROOM_CATEGORY  # noqa: PLC0415

    ravine = search_object_by_tag(f"{ZONE}:ravine", category=ROOM_CATEGORY)
    if not ravine:
        return
    ravine_room = ravine[0]
    if not ravine_room.tags.has(_RAVINE_MOUTH_ALIAS, category=ROOM_CATEGORY):
        ravine_room.tags.add(_RAVINE_MOUTH_ALIAS, category=ROOM_CATEGORY)

    # Forward exit lives in the Wilderness ravine mouth; skip silently if the
    # Wilderness is not built yet (it is, in the canonical build order).
    mouth = search_object_by_tag("wilderness:ravine_mouth", category=ROOM_CATEGORY)
    if not mouth:
        return
    if search_object_by_tag(_ENTER_EXIT_ID, category=EXIT_CATEGORY):
        return  # already wired (by this hook or the Wilderness build)
    exit_obj = create.create_object(
        "typeclasses.exits.Exit",
        key="enter",
        location=mouth[0],
        destination=ravine_room,
        aliases=["e", "east"],
    )
    exit_obj.tags.add(_ENTER_EXIT_ID, category=EXIT_CATEGORY)
