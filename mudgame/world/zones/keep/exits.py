"""Keep exits (zones spec docs/specs/zones/keep.md).

Intra-Keep connectivity is declared once as bidirectional ``_LINKS`` and
expanded to the full directed ``EXITS`` list with matching reverse exits, so
every passage can be walked both ways. The single inter-zone exit (Main Gate →
Wilderness) is one-way here; the Wilderness zone supplies the return.

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

# Bidirectional intra-Keep links: (from_key, direction_from, to_key).
# The gate spine runs south->north; the Outer Bailey is the lower-ward hub,
# with Fountain Square and the Smithy Yard as secondary hubs; the Inner Bailey
# (recall) sits beyond the inner gate.
_LINKS: list[tuple[str, str, str]] = [
    # gate spine
    ("main_gate", "n", "gatehouse"),
    ("gatehouse", "n", "entry_yard"),
    ("entry_yard", "n", "outer_bailey"),
    # outer bailey ring + spokes
    ("outer_bailey", "e", "east_wall"),
    ("outer_bailey", "w", "west_wall"),
    ("outer_bailey", "ne", "fountain_sq"),
    ("outer_bailey", "nw", "smith_yard"),
    ("outer_bailey", "se", "tavern"),
    ("outer_bailey", "sw", "provisioner"),
    ("outer_bailey", "n", "inner_gate"),
    # fountain square cluster
    ("fountain_sq", "n", "inn"),
    ("fountain_sq", "s", "bank"),
    ("fountain_sq", "e", "guild"),
    ("fountain_sq", "w", "chapel_nave"),
    ("fountain_sq", "se", "trader"),
    # smithy yard cluster
    ("smith_yard", "n", "armorer"),
    ("smith_yard", "e", "weaponsmith"),
    ("smith_yard", "w", "stables"),
    ("smith_yard", "s", "bailiff"),
    ("smith_yard", "nw", "warehouse"),
    # chapel
    ("chapel_nave", "n", "chapel_vestry"),
    ("chapel_nave", "u", "chapel_bell"),
    # inner ward
    ("inner_gate", "n", "inner_bailey"),
    ("inner_bailey", "e", "audience"),
    ("inner_bailey", "u", "keep_tower"),
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

# Inter-zone: the Main Gate opens south onto the Wilderness (keep road). The
# return exit is defined by the Wilderness zone.
EXITS.append(
    {
        "from": "main_gate",
        "dir": "s",
        "to": "wilderness:keep_road",
        "aliases": ["south", "gate", "out"],
    }
)
