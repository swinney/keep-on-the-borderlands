"""Wilderness static NPCs.

Pure data — no Evennia imports. PLACEMENT maps each NPC key to the room key
it occupies (parallel to the Keep's npcs.py pattern).
"""

from __future__ import annotations

from world.zones.records import NpcRecord

NPCS: list[NpcRecord] = [
    {
        "key": "mad_hermit",
        "name": "The Mad Hermit",
        "sdesc": "a wild-eyed hermit",
        "role": "encounter",
        "giver_key": "mad_hermit",
        "dialogue": {
            "default": (
                "He mutters about visions of chaos and a great Shrine to the east, "
                "his eyes never quite focusing."
            ),
            "quest": (
                "He offers to 'guide' you somewhere safe — toward the Shrine, "
                "if you follow his rambling directions."
            ),
        },
    },
]

# NPC key -> wilderness room key
PLACEMENT: dict[str, str] = {
    "mad_hermit": "hermit_hut",
}
