"""Orc lair exits — Cave B (Vile Rune) and Cave C (Decapitator).

Entrance links off the ravine's north ledge:
  Cave B (orc_vol): north  from ravine_north
  Cave C (orc_dec): northeast from ravine_north

Per the caves spec §ravine, the north ledge holds three cave mouths (A, B, C);
kobold is at northwest, Vile Rune at north, Decapitator at northeast.

Pure data — no Evennia import.
"""

from __future__ import annotations

from world.zones.caves._hub import expand
from world.zones.records import ExitRecord

_LINKS: list[tuple[str, str, str]] = [
    # ── Cave B — Vile Rune entrance off the north ledge ─────────────────
    ("ravine_north", "n", "orc_vol_mouth"),
    # internal Cave B layout
    ("orc_vol_mouth", "n", "orc_vol_guard"),
    ("orc_vol_guard", "e", "orc_vol_barracks"),
    ("orc_vol_guard", "n", "orc_vol_warrens"),
    ("orc_vol_warrens", "w", "orc_vol_shaman"),
    ("orc_vol_warrens", "n", "orc_vol_war_room"),
    ("orc_vol_war_room", "e", "orc_vol_chief"),
    # ── Cave C — Decapitator entrance off the north ledge ────────────────
    ("ravine_north", "ne", "orc_dec_mouth"),
    # internal Cave C layout
    ("orc_dec_mouth", "n", "orc_dec_guard"),
    ("orc_dec_guard", "n", "orc_dec_hall"),
    ("orc_dec_hall", "e", "orc_dec_totem"),
    ("orc_dec_hall", "w", "orc_dec_shaman"),
    ("orc_dec_hall", "n", "orc_dec_prison"),
    ("orc_dec_prison", "e", "orc_dec_chief"),
]

EXITS: list[ExitRecord] = expand(_LINKS)
