"""Minotaur maze exits — Cave H (the Minotaur's Maze).

Entrance link off the ravine's southern ledges (caves spec §ravine,
``ravine_south`` holds mouths F, G, H).  The H entrance drops ``d`` (down) from
``ravine_south`` — the "passage that bores deeper into the earth" in the ravine
south description.

The deep passage at the maze end exits one-way to ``shrine:shrine_gate``
(inter-zone; the Shrine zone wires the reverse exit in its own build).

Pure data — no Evennia import.
"""

from __future__ import annotations

from world.zones.caves._hub import DIR_ALIASES, expand
from world.zones.records import ExitRecord

_LINKS: list[tuple[str, str, str]] = [
    # ── Cave H — entrance off the southern ledges (down) ─────────────────
    ("ravine_south", "d", "minotaur_mouth"),
    # ── Internal maze layout ──────────────────────────────────────────────
    ("minotaur_mouth", "w", "minotaur_west_passage"),
    ("minotaur_mouth", "n", "minotaur_north_passage"),
    ("minotaur_north_passage", "n", "minotaur_crossing"),
    ("minotaur_crossing", "w", "minotaur_heart"),
    ("minotaur_crossing", "n", "minotaur_shrine_passage"),
]

EXITS: list[ExitRecord] = expand(_LINKS)

# One-way inter-zone exit: deep passage → Shrine gate.
# The Shrine zone (M11) wires the reverse from shrine:shrine_gate back here.
EXITS.append(
    {
        "from": "minotaur_shrine_passage",
        "dir": "d",
        "to": "shrine:shrine_gate",
        "aliases": DIR_ALIASES["d"],
    }
)
