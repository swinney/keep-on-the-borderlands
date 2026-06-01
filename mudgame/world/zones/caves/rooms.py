"""Caves of Chaos rooms (zones spec docs/specs/zones/caves.md).

The M9 vertical slice builds the ravine hub (the zone's spine, off which every
lair opens) plus **Cave A — the kobold lair**. The remaining lairs (B-H) attach
to the existing ravine ledges in M10, so this data is purely additive there.

The open-air ravine rooms are lit; every kobold lair room is ``dark`` — light
(a torch or the *light* spell) is required to fight there (caves spec §systems).

Pure data — no Evennia import.
"""

from __future__ import annotations

from world.zones.records import RoomRecord

ZONE = "caves"

ROOMS: list[RoomRecord] = [
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
    # ── Cave A — the kobold lair (caves spec §Cave A) ────────────────────
    {
        "key": "kobold_mouth",
        "name": "Kobold Cave Mouth",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A low, reeking tunnel scarcely high enough to stand in, the floor "
            "slick with refuse. Crude alarm-strings of bone and tin are strung "
            "across the dark at shin height. Kobold sentries skulk in niches "
            "here; the warren runs deeper to the north."
        ),
    },
    {
        "key": "kobold_guard",
        "name": "Kobold Guard Post",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A widening of the tunnel where the tribe posts its watch. A "
            "battered gong hangs ready to rouse the whole warren. Side passages "
            "branch east to a stench of dog, and north toward the press of the "
            "warren proper."
        ),
    },
    {
        "key": "kobold_kennels",
        "name": "The Kennels",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A filthy den of gnawed bones and matted straw where the kobolds "
            "keep their guard dogs. The half-starved pack snarls at any scent "
            "that is not kobold. The guard post lies back to the west."
        ),
    },
    {
        "key": "kobold_warren",
        "name": "The Kobold Warren",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A vaulted cavern teeming with kobolds — warriors, squalling young, "
            "and scuttling females packed in reeking heaps. The noise is a "
            "constant chitter. A narrow crack leads west to the shaman's grotto; "
            "the chief's den lies guarded to the north."
        ),
    },
    {
        "key": "kobold_grotto",
        "name": "Grik's Grotto",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A smoke-stained nook hung with fetishes of feather and bone, lit "
            "(when lit at all) by a guttering green fire. Here Grik, the kobold "
            "shaman, mutters over his charms. The warren lies back east."
        ),
    },
    {
        "key": "kobold_den",
        "name": "Sharptooth's Den",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "The deepest chamber of the lair, where Sharptooth the chief broods "
            "atop a heap of plundered coin and gnawed trophies. A captive sits "
            "bound and wretched in the corner, hoping for rescue. The warren "
            "lies back to the south."
        ),
    },
]
