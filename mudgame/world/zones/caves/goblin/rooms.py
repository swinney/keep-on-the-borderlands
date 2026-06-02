"""Goblin lair rooms (zones spec docs/specs/zones/caves.md §Cave D).

Cave D — the goblin lair — opens off the ravine's central scree and runs
inward to the chief's throne room, with a side cave housing the allied ogre.
Every goblin lair room is ``dark`` — light is required to fight there.

Pure data — no Evennia import.
"""

from __future__ import annotations

from world.zones.caves._hub import ZONE
from world.zones.records import RoomRecord

ROOMS: list[RoomRecord] = [
    # ── Cave D — the goblin lair (caves spec §Cave D) ────────────────────
    {
        "key": "goblin_mouth",
        "name": "Goblin Cave Mouth",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A wide, low-ceilinged tunnel stinking of wolf-musk and unwashed "
            "bodies. Crude torches of bundled grass smoulder in iron brackets, "
            "throwing more smoke than light. Goblin sentries lurk in the shadows "
            "at shin height, and the yapping of wolves echoes deeper within."
        ),
    },
    {
        "key": "goblin_guard",
        "name": "Goblin Guard Chamber",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A vaulted antechamber where the goblin watch-gang keeps its post. "
            "A battered war-drum hangs on a peg, ready to raise the alarm. "
            "The rank smell of wolf-pens drifts from the east; the main hall "
            "of the warren gapes to the north."
        ),
    },
    {
        "key": "goblin_pens",
        "name": "The Wolf Pens",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A low cavern ringed by crude stake fences where the goblins keep "
            "their wolf-mounts. The pack circles restlessly, yellow eyes "
            "gleaming. Gnawed bones litter the floor. The guard chamber lies "
            "back to the west."
        ),
    },
    {
        "key": "goblin_hall",
        "name": "The Goblin Hall",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A broad, smoke-blackened cavern that serves as the heart of the "
            "goblin warren. Warriors squat around dung-fires, sharpening blades "
            "and squabbling over scraps. Side passages open west to the "
            "shaman's grotto and east to the inner warrens; the chief's throne "
            "chamber lies north."
        ),
    },
    {
        "key": "goblin_grotto",
        "name": "Yeek's Grotto",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A cramped, reeking alcove plastered with wolf-skulls and crude "
            "hex-marks scratched into the stone. Yeek the shaman crouches here "
            "over a bubbling clay pot, muttering curses. The hall lies back "
            "to the east."
        ),
    },
    {
        "key": "goblin_warrens",
        "name": "The Inner Warrens",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A warren of low burrows carved into the soft rock, where goblin "
            "females, young, and off-duty warriors huddle in the dark. The "
            "press of bodies is oppressive. The hall is back to the west."
        ),
    },
    {
        "key": "goblin_throne",
        "name": "Snagg's Throne Room",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "The largest chamber in the lair, its walls daubed with crude "
            "pictograms of goblin victories. Snagg the chief holds court from "
            "a throne of lashed-together bones, flanked by his bodyguard. "
            "A side passage bores east into the ogre's private den; the hall "
            "lies south."
        ),
    },
    {
        "key": "ogre_den",
        "name": "The Ogre's Den",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A cavernous side-chamber whose low ceiling is scored with the "
            "marks of something very large moving in very little headroom. "
            "Smashed furniture, cracked shields, and a heap of plundered coin "
            "fill the corners. The ogre regards any intruder with profound "
            "displeasure. The throne room lies back to the west."
        ),
    },
]
