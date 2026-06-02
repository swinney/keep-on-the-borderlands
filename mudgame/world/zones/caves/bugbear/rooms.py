"""Bugbear lair rooms (zones spec docs/specs/zones/caves.md §Cave F).

Cave F — the bugbear lair — opens off the ravine's south ledge. Bugbears are
stealthy ambush hunters; the passage narrows before widening to their barracks,
giving them a natural choke-point. Every bugbear room is ``dark``.

Pure data — no Evennia import.
"""

from __future__ import annotations

from world.zones.caves._hub import ZONE
from world.zones.records import RoomRecord

ROOMS: list[RoomRecord] = [
    # ── Cave F — the bugbear lair (caves spec §Cave F) ───────────────────
    {
        "key": "bugbear_mouth",
        "name": "Bugbear Cave Mouth",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A wide, low-ceilinged entrance reeking of wet fur and old blood. "
            "The floor is packed earth worn smooth by heavy footfalls. Claw "
            "marks gouge the walls near the entrance — a territorial warning. "
            "The passage continues north into deeper darkness."
        ),
    },
    {
        "key": "bugbear_passage",
        "name": "The Ambush Passage",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A long, crooked passage where the shadows pool thick. Every alcove "
            "and jag in the stone could hide a crouching bugbear. The reek of "
            "their musk hangs in the still air. The cave mouth lies south; the "
            "barracks open north."
        ),
    },
    {
        "key": "bugbear_barracks",
        "name": "The Bugbear Barracks",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A vaulted chamber strewn with hides, gnawed bones, and the "
            "wreckage of plundered carts. Bugbear maulers sprawl and sharpen "
            "blades here between raids. Passages branch east to a guarded cell, "
            "west to a storeroom stacked with stolen goods, and north toward "
            "the shaman's den."
        ),
    },
    {
        "key": "bugbear_hold",
        "name": "The Prisoner's Cell",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A low side-cave sealed with a crude iron grate. A frightened "
            "merchant sits chained to a staple in the wall, his trade-goods "
            "long since stripped. He flinches at the light. The barracks lie "
            "back to the west."
        ),
    },
    {
        "key": "bugbear_treasury",
        "name": "The Stolen Hoard",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A rough storeroom crammed with the spoils of many raids: broken "
            "cart-wheels, bolts of trade-cloth, cracked crates of salted "
            "provisions, and a battered strong-box beneath a tangle of rope. "
            "The barracks lie back east."
        ),
    },
    {
        "key": "bugbear_shaman",
        "name": "Hrak's Den",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A smoke-blackened chamber where Hrak the bugbear shaman keeps his "
            "grotesque fetishes — skulls of humanoids mounted on spikes, "
            "bundles of dried entrails, and a smouldering fire-pit of green "
            "coals. Tribal magic and bone-charms hang from every surface. The "
            "barracks lie south; Grosh's lair is east."
        ),
    },
    {
        "key": "bugbear_chief",
        "name": "Grosh's Lair",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "The deepest chamber of the lair, dominated by a great carved "
            "throne of scavenged wood and iron. Grosh the chief lounges here "
            "amid piled coin and stolen finery, attended by the tribe's "
            "mightiest maulers. The shaman's den lies back to the west."
        ),
    },
]
