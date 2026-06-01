"""Caves of Chaos exits (zones spec docs/specs/zones/caves.md).

Intra-zone connectivity is declared once as bidirectional ``_LINKS`` and
expanded to directed ``EXITS`` (both ways), so every passage is walkable in both
directions. The inter-zone link to the Wilderness is asymmetric: the return
exit (caves → ``wilderness:ravine_mouth``) lives here, while the forward exit
(wilderness → caves) is created by ``build()`` because the Wilderness zone is
built first and cannot yet see the caves rooms (see build.py).

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

# Bidirectional intra-caves links: (from_key, direction_from, to_key).
# The ravine floor is the hub; ledges branch off it; Cave A (the kobolds) opens
# off the north ledge and runs inward to the chief's den.
_LINKS: list[tuple[str, str, str]] = [
    # ravine spine
    ("ravine", "n", "ravine_north"),
    ("ravine", "e", "ravine_mid"),
    ("ravine", "s", "ravine_south"),
    # Cave A — kobold lair, opening off the north ledge
    ("ravine_north", "nw", "kobold_mouth"),
    ("kobold_mouth", "n", "kobold_guard"),
    ("kobold_guard", "e", "kobold_kennels"),
    ("kobold_guard", "n", "kobold_warren"),
    ("kobold_warren", "w", "kobold_grotto"),
    ("kobold_warren", "n", "kobold_den"),
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

# Inter-zone: the ravine floor opens west back onto the Wilderness ravine mouth.
# The forward exit (wilderness -> caves) is wired in build.py.
EXITS.append(
    {
        "from": "ravine",
        "dir": "w",
        "to": "wilderness:ravine_mouth",
        "aliases": ["west", "out"],
    }
)
