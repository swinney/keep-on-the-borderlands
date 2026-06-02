"""Gnoll lair exits — Cave G (Hrrl's gnolls + the Owlbear).

Entrance link off the ravine's southern ledges (caves spec §ravine,
``ravine_south`` holds mouths F, G, H).  Cave F (bugbear) uses east;
Cave G (gnoll) attaches south.

Pure data — no Evennia import.
"""

from __future__ import annotations

from world.zones.caves._hub import expand
from world.zones.records import ExitRecord

_LINKS: list[tuple[str, str, str]] = [
    # ── Cave G — entrance off the southern ledges ─────────────────────────
    ("ravine_south", "s", "gnoll_mouth"),
    # internal Cave G layout
    ("gnoll_mouth", "n", "gnoll_entry"),
    ("gnoll_entry", "n", "gnoll_raider_hall"),
    ("gnoll_raider_hall", "e", "gnoll_hyena_pit"),
    ("gnoll_raider_hall", "w", "gnoll_shaman"),
    ("gnoll_raider_hall", "n", "gnoll_chief"),
    ("gnoll_chief", "w", "gnoll_owlbear_den"),
]

EXITS: list[ExitRecord] = expand(_LINKS)
