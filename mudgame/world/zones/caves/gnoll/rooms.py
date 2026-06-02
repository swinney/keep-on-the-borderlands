"""Gnoll lair rooms — Cave G (Hrrl's gnolls + the Owlbear).

Cave G is a mid-size lair (7 rooms) housing one of the ravine's most brutal
tribes.  Gnolls are hyena-headed raiders who tear through the wilderness in
murderous war-bands; their constant feud with the goblin tribe (Cave D) is the
second great inter-tribe rivalry in the Caves of Chaos.  A caged owlbear
occupies a side cave off Hrrl's throne room — a trophy-beast the gnolls keep
half-starved as a guard.  Mange the shaman squats in her den off the raider
hall, tending to dark ritual.

Cave G — Gnolls (`gnoll`, 7 rooms).  Attaches south from ``ravine_south``
(caves spec §ravine, southern ledges hold mouths F, G, H).

All lair rooms are ``dark`` (caves spec §systems).
Pure data — no Evennia import.
"""

from __future__ import annotations

from world.zones.caves._hub import ZONE
from world.zones.records import RoomRecord

ROOMS: list[RoomRecord] = [
    # ── Cave G — Gnolls (caves spec §Cave G) ─────────────────────────────
    {
        "key": "gnoll_mouth",
        "name": "Gnoll Cave Mouth",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A broad, ragged opening in the southern face of the ravine's lower "
            "ledges.  The reek of fresh hides and old blood rolls out from the "
            "darkness within.  Gnawed bones and the broken hafts of spears litter "
            "the ground outside — evidence of patrols that left and did not bother "
            "to clean up.  The ravine lies north."
        ),
    },
    {
        "key": "gnoll_entry",
        "name": "Entry Passage",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A rough-walled tunnel slopes downward, widening as it goes.  Crude "
            "torch sconces driven into the rock hold nothing — gnolls see well "
            "enough without them.  Claw-marks scar the walls at shoulder height, "
            "some fresher than others.  The cave mouth lies south; the raider "
            "hall opens north."
        ),
    },
    {
        "key": "gnoll_raider_hall",
        "name": "Raider Hall",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "The tribe's main den: a high-ceilinged chamber reeking of wet fur "
            "and offal.  Stolen goods are piled haphazardly along the walls — "
            "cloth, tools, crates — and gnoll raiders sprawl across them in "
            "various states of readiness.  A hyena pit yawns east; Mange's den "
            "lies west; Hrrl's throne is north."
        ),
    },
    {
        "key": "gnoll_hyena_pit",
        "name": "Hyena Pit",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A sunken side chamber that stinks of animal musk and old meat.  "
            "Three large hyenas pace the pit, chained loosely to iron rings in "
            "the floor — enough slack to lunge at the entrance.  The bones of "
            "at least two humanoids are scattered among the chains.  The raider "
            "hall lies west."
        ),
    },
    {
        "key": "gnoll_shaman",
        "name": "Mange's Den",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A low side chamber thick with the smoke of smoldering bones and "
            "bitter herbs.  Mange the shaman crouches over a fire-pit ringed "
            "with hyena skulls, her matted hide-robe crusted with old blood.  "
            "Strings of teeth and claws dangle from the ceiling; a leather "
            "satchel bulging with fetishes sits within easy reach.  The raider "
            "hall lies east."
        ),
    },
    {
        "key": "gnoll_chief",
        "name": "Hrrl's Throne Room",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "Hrrl the chief holds court in a broad, low-vaulted hall.  He sits "
            "on a crude throne assembled from the wreckage of caravan wagons, "
            "flanked by two snarling gnoll bodyguards.  A heavy iron strongbox "
            "rests against the far wall, padlocked shut.  A side passage to the "
            "west leads to a deep recess where something very large breathes in "
            "the dark.  The raider hall lies south."
        ),
    },
    {
        "key": "gnoll_owlbear_den",
        "name": "Owlbear's Den",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A rough-walled recess that smells of blood and broken feathers.  "
            "The owlbear paces the length of its heavy chain, feathers slick "
            "with old wounds, beak clicking in agitation.  The gnolls keep it "
            "hungry.  Bones litter the floor — previous prey — and beneath them, "
            "half-buried in the detritus, glints the dull shine of old coin and "
            "a gem or two.  Hrrl's throne room lies east."
        ),
    },
]
