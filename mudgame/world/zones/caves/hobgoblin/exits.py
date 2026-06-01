"""Hobgoblin lair exits (zones spec docs/specs/zones/caves.md §Cave E).

Cave E opens from the ravine's central scree (``ravine_mid``) and extends ten
rooms inward. The entrance is wired by tag lookup — the builder resolves
``ravine_mid`` at build time so the hub needs no per-tribe edit.

Pure data — no Evennia import.
"""

from __future__ import annotations

from world.zones.caves._hub import expand
from world.zones.records import ExitRecord

# Bidirectional links: (from_key, direction_from, to_key).
# Cave E opens off the central scree's northeast face.
_LINKS: list[tuple[str, str, str]] = [
    # entrance off the ravine's central scree
    ("ravine_mid", "ne", "hobgoblin_gate"),
    # gate -> main hall
    ("hobgoblin_gate", "n", "hobgoblin_hall"),
    # hall branches: east barracks, west mess, north inner passage
    ("hobgoblin_hall", "e", "hobgoblin_barracks"),
    ("hobgoblin_hall", "w", "hobgoblin_mess"),
    ("hobgoblin_hall", "n", "hobgoblin_inner"),
    # mess -> quarters (north, rear civilian area)
    ("hobgoblin_mess", "n", "hobgoblin_quarters"),
    # inner passage branches: east armory, west shaman, north guard room
    ("hobgoblin_inner", "e", "hobgoblin_armory"),
    ("hobgoblin_inner", "w", "hobgoblin_shaman"),
    ("hobgoblin_inner", "n", "hobgoblin_guard"),
    # guard room -> throne (innermost)
    ("hobgoblin_guard", "n", "hobgoblin_throne"),
]

EXITS: list[ExitRecord] = expand(_LINKS)
