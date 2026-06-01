"""Kobold lair rooms (zones spec docs/specs/zones/caves.md §Cave A).

Cave A — the kobold lair — opens off the ravine's north ledge and runs inward
to the chief's den. Every kobold lair room is ``dark`` — light (a torch or the
*light* spell) is required to fight there (caves spec §systems).

Pure data — no Evennia import.
"""

from __future__ import annotations

from world.zones.caves._hub import ZONE
from world.zones.records import RoomRecord

ROOMS: list[RoomRecord] = [
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
