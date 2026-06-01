"""Hobgoblin lair rooms (zones spec docs/specs/zones/caves.md §Cave E).

Cave E — the hobgoblin lair — opens off the ravine's central scree and runs
inward ten rooms deep to King Nardo's throne. The hobgoblins are the most
organised tribe: their cave is fortified, their sentries disciplined, and their
interior divided into distinct functional areas. Every room is ``dark`` (caves
spec §systems).

Pure data — no Evennia import.
"""

from __future__ import annotations

from world.zones.caves._hub import ZONE
from world.zones.records import RoomRecord

ROOMS: list[RoomRecord] = [
    # ── Cave E — the hobgoblin lair (caves spec §Cave E) ─────────────────
    {
        "key": "hobgoblin_gate",
        "name": "Hobgoblin Gate",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A wide, stone-lined throat of a cave, deliberately widened and "
            "shored with rough-cut timber. Murder holes have been chipped into "
            "the ceiling, and a heavy iron bar stands ready to seal the inner "
            "passage. Hobgoblin sentries hold the mouth in practiced silence; "
            "noise carries badly here, which is exactly how they want it."
        ),
    },
    {
        "key": "hobgoblin_hall",
        "name": "The Entry Hall",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A broad vaulted hall just inside the gate, torchlit with smoky "
            "pine brands set in iron rings. Passages branch east to the "
            "barracks, west to the mess, and north deeper into the lair. "
            "Hobgoblin soldiers form up here before sorties; a duty-roster is "
            "scratched into the stone near the torch-stand."
        ),
    },
    {
        "key": "hobgoblin_barracks",
        "name": "The Barracks",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A long, low room of stone-slab bunks and weapon racks. Spears, "
            "short swords, and shields are racked in numbered order — the "
            "hobgoblins are meticulous about kit. Off-duty soldiers sleep in "
            "rotation here, armour never fully off. The hall lies back to the "
            "west."
        ),
    },
    {
        "key": "hobgoblin_mess",
        "name": "Mess Hall",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "Rough-hewn benches and a split-log table hold the remnants of the "
            "tribe's communal meal: bones, gristle, and a cracked clay pot of "
            "something foul-smelling. The hall lies back to the east; a low "
            "arch at the far end leads north to the inner quarters."
        ),
    },
    {
        "key": "hobgoblin_quarters",
        "name": "Inner Quarters",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A cramped rear chamber curtained off with skins, where hobgoblin "
            "females and young are kept well away from fighting ground. The "
            "mood here is sullen; a captive, wrists bound, slumps against the "
            "far wall in the dark. The mess hall lies back to the south."
        ),
    },
    {
        "key": "hobgoblin_inner",
        "name": "Inner Passage",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A T-shaped junction where the lair's rear corridors meet. The "
            "air is drier here — the cave bores deeper north toward the king's "
            "chambers. An arched side-passage to the east reeks of old iron; "
            "to the west a guttering candle marks Vurt's door. The entry hall "
            "lies back to the south."
        ),
    },
    {
        "key": "hobgoblin_armory",
        "name": "The Armory",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A dry stone chamber stacked with reserve arms: bundled crossbow "
            "bolts, extra spearheads, coils of rope, and a locked chest of "
            "oil flasks. A single hobgoblin soldier keeps inventory with a "
            "tally-stick. The inner passage lies back to the west."
        ),
    },
    {
        "key": "hobgoblin_shaman",
        "name": "Vurt's Chamber",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A low room choked with acrid smoke from a brazier of coals and "
            "bone dust. Dried bat wings and humanoid finger-bones hang on "
            "strings from the ceiling. Here Vurt, the hobgoblin shaman, "
            "communes with the dark spirits he claims to control. His gaze "
            "misses nothing. The inner passage lies back to the east."
        ),
    },
    {
        "key": "hobgoblin_guard",
        "name": "The Guard Room",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A square chamber posted with King Nardo's elite guard: scarred "
            "veterans in full chain mail, shields braced. The only way north "
            "is through them. They do not parley and they do not retreat. The "
            "inner passage lies back to the south."
        ),
    },
    {
        "key": "hobgoblin_throne",
        "name": "King Nardo's Throne Room",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "The deepest chamber, hewn wide by generations of hobgoblin "
            "labour. A crude throne of stacked stone and iron plate occupies "
            "the far wall, and before it King Nardo stands — or paces — with "
            "the coiled patience of a commander who has never lost a battle he "
            "chose. A great iron strongbox is chained to the throne's base, "
            "and a weapon of unusual workmanship leans against its lid. The "
            "guard room lies back to the south."
        ),
    },
]
