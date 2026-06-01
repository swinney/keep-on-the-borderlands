"""Shared ravine hub for the Caves of Chaos (zones spec docs/specs/zones/caves.md).

The ravine is the zone's spine: an open-air gulch off which every tribal lair
opens. It is built once, before any tribe, and owns the inter-zone link back to
the Wilderness. Each tribe subpackage (discovered at build time) attaches its
own rooms/exits to this hub.

The hub also carries the direction-reversal helpers (``REVERSE`` / ``DIR_ALIASES``
/ ``_expand``) so every tribe can declare its exits as bidirectional links and
expand them the same way.

Pure data — Evennia is imported lazily inside :func:`build`, so importing this
module stays Evennia-free for the pure-data test suites.
"""

from __future__ import annotations

from world.zones.records import ExitRecord, RoomRecord

ZONE = "caves"

# direction -> its reverse, for auto-generating return exits.
REVERSE: dict[str, str] = {
    "n": "s",
    "s": "n",
    "e": "w",
    "w": "e",
    "ne": "sw",
    "sw": "ne",
    "nw": "se",
    "se": "nw",
    "u": "d",
    "d": "u",
}

# Human-readable aliases so players can type full direction names.
DIR_ALIASES: dict[str, list[str]] = {
    "n": ["north"],
    "s": ["south"],
    "e": ["east"],
    "w": ["west"],
    "ne": ["northeast"],
    "nw": ["northwest"],
    "se": ["southeast"],
    "sw": ["southwest"],
    "u": ["up"],
    "d": ["down"],
}


def expand(links: list[tuple[str, str, str]]) -> list[ExitRecord]:
    """Expand bidirectional links into directed exit records (both ways)."""
    out: list[ExitRecord] = []
    for src, direction, dst in links:
        out.append({"from": src, "dir": direction, "to": dst, "aliases": DIR_ALIASES[direction]})
        rev = REVERSE[direction]
        out.append({"from": dst, "dir": rev, "to": src, "aliases": DIR_ALIASES[rev]})
    return out


HUB_ROOMS: list[RoomRecord] = [
    # ── The ravine (hub spine; caves spec "The ravine") ──────────────────
    {
        "key": "ravine",
        "name": "The Ravine Floor",
        "zone": ZONE,
        "desc": (
            "A steep-sided gulch of trampled earth and bone-litter, the very "
            "heart of the Caves of Chaos. Dark cave mouths gape from the rock "
            "on every side, and unseen sentries watch the open ground — anyone "
            "crossing here does so in a crossfire. The way back to the "
            "wilderness lies west; ledges climb north and drop away south."
        ),
    },
    {
        "key": "ravine_north",
        "name": "North Ledges",
        "zone": ZONE,
        "desc": (
            "A shelf of broken rock along the ravine's northern wall, reached "
            "by a scramble up from the floor. Three cave mouths open here; the "
            "nearest, low and rank with a kennel-stink, breathes out the yips "
            "and chatter of kobolds to the northwest."
        ),
    },
    {
        "key": "ravine_mid",
        "name": "Central Scree",
        "zone": ZONE,
        "desc": (
            "A slope of loose scree across the middle of the ravine, where two "
            "more cave mouths wait in the eastern rock. Loose stones betray any "
            "footstep. The ravine floor lies west."
        ),
    },
    {
        "key": "ravine_south",
        "name": "South Ledges",
        "zone": ZONE,
        "desc": (
            "The ravine narrows southward to a huddle of lower ledges and "
            "darker mouths. A foul draught wells up from a passage that bores "
            "deeper into the earth, away from the light. The floor lies north."
        ),
    },
]

# Bidirectional ravine-spine links: (from_key, direction_from, to_key).
_HUB_LINKS: list[tuple[str, str, str]] = [
    ("ravine", "n", "ravine_north"),
    ("ravine", "e", "ravine_mid"),
    ("ravine", "s", "ravine_south"),
]

HUB_EXITS: list[ExitRecord] = expand(_HUB_LINKS)

# Inter-zone: the ravine floor opens west back onto the Wilderness ravine mouth.
# The forward exit (wilderness -> caves) is wired in build() below.
HUB_EXITS.append(
    {
        "from": "ravine",
        "dir": "w",
        "to": "wilderness:ravine_mouth",
        "aliases": ["west", "out"],
    }
)

# Stable identity of the ravine-mouth crossing, shared with the Wilderness zone
# so whichever zone builds last finds and reuses the existing exit.
_ENTER_EXIT_ID = "wilderness:ravine_mouth:enter"
_RAVINE_MOUTH_ALIAS = "caves:ravine_mouth"


def build() -> None:
    """Create/update the ravine hub's rooms and exits and link to the Wilderness."""
    from world.zones import builder  # noqa: PLC0415 (lazy: defer Evennia import)

    builder.build_zone(ZONE, HUB_ROOMS, HUB_EXITS)
    _link_to_wilderness()


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
