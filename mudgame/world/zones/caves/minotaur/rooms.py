"""Minotaur maze rooms — Cave H (the Minotaur's Maze).

Cave H is a cramped, disorienting labyrinth beneath the southern ledges of the
ravine.  A solitary minotaur stalks its passages, drawn to intruders by the
echoes that carry through the stone.  At the maze's heart lies the beast's
accumulated hoard; a deep passage beyond leads to the Shrine of Evil Chaos.

Cave H attaches downward from ``ravine_south`` (caves spec §ravine, southern
ledges hold mouths F, G, H; the H entry "bores deeper into the earth").

All lair rooms are ``dark`` (caves spec §systems).
Pure data — no Evennia import.
"""

from __future__ import annotations

from world.zones.caves._hub import ZONE
from world.zones.records import RoomRecord

ROOMS: list[RoomRecord] = [
    # ── Cave H — Minotaur's Maze (caves spec §Cave H) ────────────────────
    {
        "key": "minotaur_mouth",
        "name": "Descending Passage",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A rough-cut passage drops steeply from the ravine floor into cold "
            "stone.  The walls narrow and the ceiling drops; the air carries the "
            "thick, musky reek of a large animal.  Crude gouges in the rock — "
            "horn-marks at head height — suggest whatever lives below passed "
            "this way often.  The ravine lies up and behind; the maze extends "
            "north."
        ),
    },
    {
        "key": "minotaur_west_passage",
        "name": "Dead-End Passage",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A side tunnel that veers west and ends abruptly in a cave-in.  "
            "The rubble pile is fresh — whatever caused it was recent.  "
            "Bones scattered near the blockage suggest this corridor was once "
            "a way deeper into the rock.  The descent lies east."
        ),
    },
    {
        "key": "minotaur_north_passage",
        "name": "Winding Passage",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "The tunnel twists without reason, changing direction twice within "
            "a dozen paces.  The walls are close; the sound of heavy breathing "
            "seems to come from every direction at once.  Deep claw-scores run "
            "along the floor, worn smooth by repeated passage.  The descent "
            "lies south; the passage continues north."
        ),
    },
    {
        "key": "minotaur_crossing",
        "name": "Maze Crossing",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "Four passages meet here in a low, vaulted chamber that smells "
            "strongly of blood and old bone.  Humanoid skulls are stacked in "
            "a rough pyramid in the center — trophies, or a waymarker the "
            "minotaur uses to orient itself.  The winding passage lies south; "
            "a wider hall opens west; the air from the north is cold and damp."
        ),
    },
    {
        "key": "minotaur_heart",
        "name": "The Maze Heart",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "The core of the labyrinth: a broad, low chamber where the "
            "minotaur lairs.  Gnawed bones cover the floor knee-deep, and "
            "amid the wreckage glitters the accumulated plunder of years — "
            "coin, rusted weapons, and a gem or two that caught the beast's "
            "eye.  The crossing lies east.  A faint, foul breeze rises from a "
            "cracked passage in the floor to the north."
        ),
    },
    {
        "key": "minotaur_shrine_passage",
        "name": "Deep Passage",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A fissure in the bedrock, just wide enough to squeeze through, "
            "descends into profound darkness.  The air rising from below is "
            "cold and carries the faint, sour smell of incense and something "
            "older.  Whatever is down there has nothing to do with the "
            "minotaur.  The maze heart lies south; the passage drops further "
            "down into the earth."
        ),
    },
]
