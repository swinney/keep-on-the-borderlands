"""Tavern roster configuration — henchmen.md §1.

Static recruit data (name, role, level, fee, morale). The Keep tavern offers
these six recruits; entries refresh on seasonal reset (henchmen.md §6).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RosterEntry:
    """A single recruit available at the tavern roster."""

    key: str  # internal identifier (stable across session)
    name: str  # display name
    role: str  # human-readable role
    level: int  # character level (0 = non-combatant porter/torchbearer)
    hire_fee: int  # upfront cost in gold pieces
    base_morale: int  # starting morale score


ROSTER: tuple[RosterEntry, ...] = (
    RosterEntry("torchbearer_01", "Pip", "Torchbearer", 0, 10, 6),
    RosterEntry("torchbearer_02", "Bram", "Torchbearer", 0, 10, 6),
    RosterEntry("footman_01", "Gorn", "Light Footman", 1, 40, 7),
    RosterEntry("footman_02", "Sera", "Light Footman", 1, 40, 7),
    RosterEntry("bowman_01", "Talin", "Bowman", 1, 60, 7),
    RosterEntry("acolyte_01", "Bro. Aldric", "Acolyte", 1, 100, 8),
)
