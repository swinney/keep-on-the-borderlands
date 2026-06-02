"""Shrine rooms (zones spec docs/specs/zones/shrine.md).

The endgame temple of the Cult of Evil Chaos beneath the Caves: ~16 rooms
descending from the Black Gate to the Inner Sanctum and its altar. Rooms below
the threshold are ``dark``; the deep rooms are additionally ``no_recall`` so the
climax stays committed (spec §Systems wiring). Pure data — no Evennia import.
"""

from __future__ import annotations

from world.zones.records import RoomRecord

ZONE = "shrine"

ROOMS: list[RoomRecord] = [
    {
        "key": "shrine_gate",
        "name": "The Black Gate",
        "zone": ZONE,
        "desc": (
            "Doors of black iron, carved over with leering skulls, stand at the "
            "end of the deep passage from the maze. Cold air sighs out of the "
            "dark beyond, carrying a reek of old blood. The way back climbs up "
            "into the minotaur's warren; the temple opens north."
        ),
    },
    {
        "key": "narthex",
        "name": "Defiled Narthex",
        "zone": ZONE,
        "desc": (
            "A pillared entry hall whose holy carvings have been chiselled into "
            "obscenities. A great warning bell hangs in an alcove, rigged to "
            "rouse the whole temple. Cult sentries keep watch where the hall "
            "opens north into the nave."
        ),
    },
    {
        "key": "nave_evil",
        "name": "Nave of Chaos",
        "zone": ZONE,
        "desc": (
            "The temple's long central nave, lit by no honest flame. Pews "
            "fashioned from human bone face a defiled chancel, and acolytes "
            "patrol the aisles in silence. Side chapels open to either hand, a "
            "stair descends to the crypts, and the inner ways run on north."
        ),
        "dark": True,
    },
    {
        "key": "side_chapel_n",
        "name": "North Chapel",
        "zone": ZONE,
        "desc": (
            "A side chapel heaped with plunder — goods looted from Keep caravans "
            "piled as a profane offering. Bolts of cloth, broached casks, and "
            "spilled coin moulder in the dark before a faceless idol."
        ),
        "dark": True,
    },
    {
        "key": "side_chapel_s",
        "name": "South Chapel",
        "zone": ZONE,
        "desc": (
            "A squat font of black stone dominates this chapel, brimming with a "
            "fluid that drinks the light. The cult fouls captured holy water "
            "here; a vial of the true stuff would hiss against its surface."
        ),
        "dark": True,
    },
    {
        "key": "crypt_upper",
        "name": "Upper Crypt",
        "zone": ZONE,
        "desc": (
            "Burial niches honeycomb the walls of this low vault, most of them "
            "broken open and empty. The things that crawled out — skeletons and "
            "shambling dead — shuffle in the dark. Stairs sink deeper still."
        ),
        "dark": True,
    },
    {
        "key": "crypt_lower",
        "name": "Lower Crypt",
        "zone": ZONE,
        "desc": (
            "The air here is grave-cold and utterly black. A sealed reliquary of "
            "lead and iron squats at the vault's heart, and the wights that ward "
            "it stir at the warmth of living blood. There is no recalling from so "
            "deep — only the stairs back up, or the dark ahead."
        ),
        "dark": True,
        "no_recall": True,
    },
    {
        "key": "cells",
        "name": "Prisoner Cells",
        "zone": ZONE,
        "desc": (
            "A row of barred cells cut into the rock, most empty, a wretched few "
            "not. Captives taken from the Keep and the caves wait here for the "
            "altar — those still strong enough to be freed press against the bars."
        ),
        "dark": True,
    },
    {
        "key": "acolyte_dorm",
        "name": "Acolyte Dormitory",
        "zone": ZONE,
        "desc": (
            "Rough cots and prayer-mats fill this dormitory where the cult's "
            "acolytes take their rest between rites. Robes hang on pegs and a "
            "censer of choking incense smoulders in the corner."
        ),
        "dark": True,
    },
    {
        "key": "adept_study",
        "name": "Adept's Study",
        "zone": ZONE,
        "desc": (
            "The Adept's private study, walls lined with blasphemous tomes and "
            "loose notes. Among the lore a careful reader might find the Shrine's "
            "password and hints of a hidden vault. A draught stirs the papers "
            "from one particular shelf."
        ),
        "dark": True,
    },
    {
        "key": "river_cavern",
        "name": "Underground River",
        "zone": ZONE,
        "desc": (
            "A black river races through this natural cavern, its current strong "
            "enough to drag the unwary under. The cult keeps a coracle moored "
            "here as a way out when the temple falls. No recall reaches through "
            "the living rock this deep."
        ),
        "dark": True,
        "no_recall": True,
    },
    {
        "key": "ritual_hall",
        "name": "Hall of Ritual",
        "zone": ZONE,
        "desc": (
            "A broad hall of black columns where the cult works its great rites. "
            "Channels in the floor run toward a central drain, dark and crusted. "
            "Galleries above offer cover for an ambush. The sanctum lies beyond; "
            "no prayer of recall carries out of this deep place."
        ),
        "dark": True,
        "no_recall": True,
    },
    {
        "key": "inner_sanctum",
        "name": "Inner Sanctum",
        "zone": ZONE,
        "desc": (
            "The holy of unholies, a vaulted chamber thick with the presence of "
            "Chaos. Here the Adept holds court before the great altar, the "
            "cult's living heart. The walls themselves seem to refuse any thought "
            "of escape — there is no recall from this place."
        ),
        "dark": True,
        "no_recall": True,
    },
    {
        "key": "altar_of_chaos",
        "name": "Altar of Evil Chaos",
        "zone": ZONE,
        "desc": (
            "A monolith of fused black stone, slick with the residue of "
            "sacrifice, radiating a cold that bites the soul. This is the engine "
            "of the cult's power; shatter it and the Shrine itself would fail. "
            "No recall reaches the foot of the altar."
        ),
        "dark": True,
        "no_recall": True,
    },
    {
        "key": "boss_lair",
        "name": "The Exposed One's Lair",
        "zone": ZONE,
        "desc": (
            "A hidden bolt-hole behind the sanctum, bare but for a cot and a "
            "strongbox. When the spy in the Keep is unmasked he flees here to "
            "make his stand among his true masters. No recall reaches this deep."
        ),
        "dark": True,
        "no_recall": True,
    },
    {
        "key": "secret_vault",
        "name": "Secret Vault",
        "zone": ZONE,
        "desc": (
            "A concealed strongroom whose door is masked in the living rock — "
            "only a sharp eye finds the seam. Within lies the cult's true "
            "treasure, hoarded against the day of Chaos. No recall reaches the "
            "vault."
        ),
        "dark": True,
        "no_recall": True,
    },
]
