"""Shrine exits (zones spec docs/specs/zones/shrine.md).

Intra-Shrine connectivity is declared once as bidirectional ``_LINKS`` and
expanded to the full directed ``EXITS`` list with matching reverse exits, so
every passage can be walked both ways. The single inter-zone exit (Black Gate →
Caves minotaur maze) is one-way here; the Caves zone supplies the descent.

Pure data — no Evennia import.
"""

from __future__ import annotations

from world.zones.records import ExitRecord

# direction -> its reverse, for auto-generating return exits.
REVERSE: dict[str, str] = {
    "n": "s",
    "s": "n",
    "e": "w",
    "w": "e",
    "ne": "sw",
    "sw": "ne",
    "nw": "se",
    "se": "nw",
    "u": "d",
    "d": "u",
}

# Human-readable aliases so players can type full direction names.
DIR_ALIASES: dict[str, list[str]] = {
    "n": ["north"],
    "s": ["south"],
    "e": ["east"],
    "w": ["west"],
    "ne": ["northeast"],
    "nw": ["northwest"],
    "se": ["southeast"],
    "sw": ["southwest"],
    "u": ["up"],
    "d": ["down"],
}

# Bidirectional intra-Shrine links: (from_key, direction_from, to_key).
# The temple descends from the Black Gate: gate -> narthex -> nave, with the
# side chapels and crypts off the nave, and the deep ways (dorm, study, ritual
# hall, river, sanctum, altar, boss lair, vault) running on north and down.
_LINKS: list[tuple[str, str, str]] = [
    # threshold spine
    ("shrine_gate", "n", "narthex"),
    ("narthex", "n", "nave_evil"),
    # nave: side chapels, the crypt stair, and the way deeper
    ("nave_evil", "w", "side_chapel_n"),
    ("nave_evil", "e", "side_chapel_s"),
    ("nave_evil", "d", "crypt_upper"),
    ("nave_evil", "n", "acolyte_dorm"),
    # crypts
    ("crypt_upper", "d", "crypt_lower"),
    ("crypt_upper", "e", "cells"),
    # cult quarters and the descent to the ritual hall
    ("acolyte_dorm", "e", "adept_study"),
    ("acolyte_dorm", "n", "ritual_hall"),
    ("adept_study", "s", "secret_vault"),
    # the deep climax
    ("ritual_hall", "d", "river_cavern"),
    ("ritual_hall", "n", "inner_sanctum"),
    ("inner_sanctum", "n", "altar_of_chaos"),
    ("inner_sanctum", "e", "boss_lair"),
]


def _expand(links: list[tuple[str, str, str]]) -> list[ExitRecord]:
    """Expand bidirectional links into directed exit records (both ways)."""
    out: list[ExitRecord] = []
    for src, direction, dst in links:
        out.append({"from": src, "dir": direction, "to": dst, "aliases": DIR_ALIASES[direction]})
        rev = REVERSE[direction]
        out.append({"from": dst, "dir": rev, "to": src, "aliases": DIR_ALIASES[rev]})
    return out


EXITS: list[ExitRecord] = _expand(_LINKS)

# Inter-zone: the Black Gate climbs up to the Caves minotaur maze's deep
# passage. The Caves minotaur exits supply the matching descent (d -> shrine).
EXITS.append(
    {
        "from": "shrine_gate",
        "dir": "u",
        "to": "caves:minotaur_shrine_passage",
        "aliases": DIR_ALIASES["u"],
    }
)
