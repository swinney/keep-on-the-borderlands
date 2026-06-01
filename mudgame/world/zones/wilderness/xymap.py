"""xyzgrid map data for the Wilderness zone.

Pure data — no Evennia imports. XYMAP_DATA is consumed by ``build()`` which
passes it to the xyzgrid contrib for room/exit creation.

Coordinate mapping (wilderness spec §2): outline_y → xyzgrid_y = outline_y + 1.
All 18 hexes land at non-negative (x, y) coords with z = "wilderness".

Note: the spec's MAPSTR had a typo in the connector row between y=1 and y=0
(8 leading spaces instead of 6, which would have placed the first pipe at
x=3 rather than x=2, dropping the glade-river_ford link). The correct row
is ``      | | |`` (6 spaces), matching the connectivity table in spec §3.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Map string — topology source of truth for xyzgrid room/exit creation.
# '#' = normal room node; 'I' = InterruptMapNode (auto-walk stops here).
# '-' = east-west link; '|' = north-south link.
# ---------------------------------------------------------------------------
MAPSTR = r"""

+ 0 1 2 3 4 5

4   #
    |
3   #-#   #
    | |   |
2   #-#-#-#-#
    | | | | |
1 #-#-#-#-#-#
      | | |
0     #-#-I

+ 0 1 2 3 4 5

"""

# ---------------------------------------------------------------------------
# Per-coordinate prototype overrides.
# Wildcard ("*","*") sets the typeclass for every room not listed explicitly.
# Specific entries set key, desc, room_key attr, and the safe flag.
# ---------------------------------------------------------------------------
_BASE: dict[str, Any] = {
    "prototype_parent": "xyz_room",
    "typeclass": "world.zones.wilderness.typeclasses.WildernessRoom",
}


def _room(name: str, desc: str, room_key: str, *, safe: bool = False) -> dict[str, Any]:
    attrs: list[tuple[str, object]] = [
        ("zone", "wilderness"),
        ("room_key", room_key),
    ]
    if safe:
        attrs.append(("safe", True))
    return {**_BASE, "key": name, "desc": desc, "attrs": attrs}


PROTOTYPES: dict[tuple[int, int] | tuple[str, str], dict[str, Any]] = {
    ("*", "*"): {
        **_BASE,
        "key": "The Wilderness",
        "desc": "Open borderlands stretch in every direction.",
        "attrs": [("zone", "wilderness")],
    },
    # y=1 row
    (0, 1): _room(
        "The Keep Road",
        "A broad track of packed earth leads north toward the Keep's gatehouse. "
        "The road is well-patrolled; travellers move freely here.",
        "keep_road",
        safe=True,
    ),
    (1, 1): _room(
        "Crossroads",
        "A weathered signpost marks the crossing. One arm points north toward "
        "the farmlands; the other east toward the ford. The Keep lies to the west.",
        "crossroads",
    ),
    (2, 1): _room(
        "River Ford",
        "A shallow crossing where the stream widens. The current runs swift "
        "after rain; the far bank is slick mud. Tracks of many creatures mark the approach.",
        "river_ford",
    ),
    (3, 1): _room(
        "Low Hills",
        "Rolling hills of scrub and boulder. Mountain lions have been seen here, "
        "sunning themselves on the flat rocks in the afternoon.",
        "hills_low",
    ),
    (4, 1): _room(
        "Raider Camp",
        "The remains of a camp — fire-pit, stake perimeter, rope lines between "
        "trees. Brigands use this as a waystation; the charcoal is fresh.",
        "raider_camp",
    ),
    (5, 1): _room(
        "Ravine Approach",
        "The hills funnel down to a narrow valley. Dark cave mouths gape in the "
        "ravine walls ahead. The air smells of old smoke and something worse.",
        "ravine_approach",
    ),
    # y=2 row
    (1, 2): _room(
        "Abandoned Farmlands",
        "Fallow fields where homesteaders once tried their luck. Rusted ploughs "
        "and rotting fence-posts mark the property lines. Something drove them off.",
        "farmlands",
    ),
    (2, 2): _room(
        "Marsh Edge",
        "The ground turns soft and treacherous. Reeds cluster in standing water; "
        "frogs fall silent as you approach. The swamp deepens to the north.",
        "marsh_edge",
    ),
    (3, 2): _room(
        "The Mad Hermit's Hut",
        "A crooked shack leans against a mossy boulder. Bones and trinkets hang "
        "from the eaves. A wild-eyed figure watches you from the doorway.",
        "hermit_hut",
    ),
    (4, 2): _room(
        "Ruined Tower",
        "A crumbling stone tower, its upper floors long collapsed. Carved symbols "
        "on the lintel are not of any local style. Strange sounds echo at night.",
        "old_tower",
    ),
    (5, 2): _room(
        "Ravine Mouth",
        "The ravine opens here. Across from you a network of cave entrances pierces "
        "the rock face — the Caves of Chaos. The air is heavy and still.",
        "ravine_mouth",
    ),
    # y=3 row
    (1, 3): _room(
        "West Woods",
        "Dense woodland where little sunlight reaches the forest floor. "
        "Thick webs glint between the trees. Something large moves in the canopy.",
        "woods_west",
    ),
    (2, 3): _room(
        "The Sunken Swamp",
        "Knee-deep black water and strangling vines. Eyes watch from below the "
        "surface. Lizard folk have been seen patrolling these murky channels.",
        "swamp",
    ),
    (4, 3): _room(
        "Borderlands Overlook",
        "A rocky promontory with a commanding view. To the east the ravine "
        "and cave mouths are visible. To the north the forest stretches away.",
        "overlook",
    ),
    # y=4 row
    (1, 4): _room(
        "Deep Woods",
        "The trees close in completely. Webs coat everything; movement is slow. "
        "The spider nest is somewhere close — the clicking and hissing are constant.",
        "woods_deep",
    ),
    # y=0 row
    (2, 0): _room(
        "Quiet Glade",
        "A sun-dappled clearing where the trees thin out. A clear stream runs "
        "through it. Travellers rest here undisturbed — something keeps the predators away.",
        "glade",
        safe=True,
    ),
    (3, 0): _room(
        "High Hills",
        "Bare rocky ridgeline with a view of the ravine to the east. A raider "
        "lookout used these heights; the remains of a fire are cold.",
        "hills_high",
    ),
    (4, 0): _room(
        "Sealed Cleft",
        "A crack in the cliff face, wide enough to squeeze through, has been "
        "deliberately barred with iron spikes and old timber. No one has passed "
        "here in a long time.",
        "sealed_cleft",
    ),
}

XYMAP_DATA: dict[str, Any] = {
    "zcoord": "wilderness",
    "map": MAPSTR,
    "prototypes": PROTOTYPES,
}
