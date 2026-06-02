"""Orc lairs — Cave B (Vile Rune) and Cave C (Decapitator).

Both orc tribes form one content unit; the rivalries between them are already
encoded in the faction/repop config (orc_vol ↔ orc_dec, tension=+24, war band;
designated rivals of one another in the repop halt). This module owns the room
data for both lairs.

Cave B — Orcs of the Vile Rune (`orc_vol`, 7 rooms).
Cave C — Orcs of the Decapitator (`orc_dec`, 7 rooms).

All lair rooms are ``dark`` (caves spec §systems).
Pure data — no Evennia import.
"""

from __future__ import annotations

from world.zones.caves._hub import ZONE
from world.zones.records import RoomRecord

ROOMS: list[RoomRecord] = [
    # ── Cave B — Orcs of the Vile Rune (caves spec §Cave B) ─────────────
    {
        "key": "orc_vol_mouth",
        "name": "Vile Rune Cave Mouth",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A wide, torchlit entrance stinking of sweat and iron. The walls "
            "are daubed with the Vile Rune — a jagged red symbol the tribe "
            "brands into its weapons and its prisoners. Two sentries slouch "
            "against the rock, eyeing the ravine with open contempt. The cave "
            "runs northward into rising noise."
        ),
    },
    {
        "key": "orc_vol_guard",
        "name": "Guard Room",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A rough chamber serving as the tribe's first line of defence. "
            "Torch-sockets are jammed into cracks in the walls, guttering "
            "orange. An eastern passage leads to the warriors' barracks; the "
            "main tunnel continues north deeper into the lair."
        ),
    },
    {
        "key": "orc_vol_barracks",
        "name": "Warriors' Barracks",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A long, low hall of straw bedding and weapon-racks. The stench of "
            "bodies is overpowering. Off-duty warriors sprawl with dice and "
            "argument; the rune-branded shields on the wall make clear whose "
            "territory this is. The guard room lies to the west."
        ),
    },
    {
        "key": "orc_vol_warrens",
        "name": "Inner Warrens",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A guarded inner chamber, loud with the screech and scramble of "
            "orc young and the sharp eyes of females watching the entrance. "
            "Warriors stand at the mouth with spears levelled — the Vile Rune "
            "tribe guards its vulnerable here with grim resolve. The shaman's "
            "den lies west; a war council room opens to the north."
        ),
    },
    {
        "key": "orc_vol_shaman",
        "name": "Mawg's Den",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A close cave dyed lurid red by dried blood and smouldering herbs. "
            "Skulls line the niches — kobold, human, and things harder to "
            "identify. Mawg, the tribe's shaman, tends a slow fire here and "
            "mutters hexes at the walls. The warrens lie back to the east."
        ),
    },
    {
        "key": "orc_vol_war_room",
        "name": "War Council Chamber",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A large chamber where the tribe's war party marshals before raids. "
            "A crudely scratched map of the ravine decorates the far wall with "
            "the Decapitator's cave marked out in vengeful slashes. The chief's "
            "chamber opens to the east; the inner warrens lie south."
        ),
    },
    {
        "key": "orc_vol_chief",
        "name": "Grukk's Chamber",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "The chief's private chamber, hung with the standards of raided "
            "caravans and the bones of rivals. A battered iron chest sits "
            "chained to the wall behind Grukk's throne-pile of cloaks and "
            "weapons. The war council chamber lies to the west. A battle-"
            "standard of the Vile Rune leans conspicuously against the throne."
        ),
    },
    # ── Cave C — Orcs of the Decapitator (caves spec §Cave C) ───────────
    {
        "key": "orc_dec_mouth",
        "name": "Decapitator Cave Mouth",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A shadowed entrance whose lintel is decorated with poles topped "
            "by the skulls of enemies — mostly kobold, with a few that look "
            "unsettlingly human. The tribe's name is earned anew each season. "
            "Guards watch the ravine northeast ledge with stone-faced hostility."
        ),
    },
    {
        "key": "orc_dec_guard",
        "name": "Guard Chamber",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A reinforced entrance chamber where the tribe musters its watch. "
            "The floor is hard-packed, the air thick with pipe smoke and old "
            "blood. The warriors here are disciplined by orc standards — they "
            "do not slouch. The passage runs north into the lair."
        ),
    },
    {
        "key": "orc_dec_hall",
        "name": "Warriors' Hall",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "The main hall of the Decapitator lair, a broad cavern where "
            "warriors drill and bicker. The western wall is the shaman's "
            "territory; the eastern passage leads to the tribe's totem chamber; "
            "a north passage descends toward the prison and the chief's den."
        ),
    },
    {
        "key": "orc_dec_totem",
        "name": "Totem Chamber",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A vaulted alcove dominated by the Decapitator Totem: the skull of "
            "a giant, mounted on a pole and hung with the scalps of fallen "
            "rivals. The elite totem guards stand here with ceremonial axes, "
            "treating the room as sacred ground. The warriors' hall lies west."
        ),
    },
    {
        "key": "orc_dec_shaman",
        "name": "Ssruk's Den",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A damp, low-roofed cell that smells of ash and iron filings. "
            "Ssruk, the Decapitator shaman, works bone-carvings by firelight "
            "and is not pleased by visitors. Ritual chalk drawings cover every "
            "surface. The warriors' hall lies back to the east."
        ),
    },
    {
        "key": "orc_dec_prison",
        "name": "Prison Pit",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "A low chamber with an iron grate set into the floor. A Keep "
            "soldier, dirty and gaunt, sits in the pit below — alive, for "
            "now. The guard stationed here leers at the entrance. A passage "
            "opens east to the chief's den."
        ),
    },
    {
        "key": "orc_dec_chief",
        "name": "Bloodtusk's Den",
        "zone": ZONE,
        "dark": True,
        "desc": (
            "The innermost chamber of the Decapitator lair, dominated by "
            "Bloodtusk — an orc of unusual size, scarred from a dozen battles "
            "against the Vile Rune tribe. Coin and plundered gear are piled "
            "carelessly in the corners; Bloodtusk needs no iron chest — he "
            "trusts only his own fists. The prison pit lies to the west."
        ),
    },
]
