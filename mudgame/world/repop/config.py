"""Repop tuning constants (R3 / docs/specs/repop.md §1).

Single tuning file for the wall-clock timing of tribe-scoped respawn and the
Shrine reset cycle. The constants for standard respawn, the leadership halt,
rival scouting, and the Shrine reset live here; the seasonal-reset constants are
added by the later M6 task that implements it.

All durations are real-world seconds (wall-clock), not game time
(docs/architecture.md §5.2).
"""

from __future__ import annotations

# Normal mob respawn delay. 15 real minutes (spec §1 STANDARD_RESPAWN).
STANDARD_RESPAWN: int = 15 * 60

# Repop freeze after a tribe's chief AND shaman are both dead at once
# (spec §1 LEADERSHIP_HALT / §3). 60 real minutes.
LEADERSHIP_HALT: int = 60 * 60

# How often the repop_manager reconciles due spawns (spec §1 MANAGER_TICK).
MANAGER_TICK: int = 60

# Number of rival mobs sent into a halted tribe's empty lair (spec §1, §4).
SCOUT_PARTY_SIZE: int = 3

# Designated rival that moves into a broken tribe's lair during its halt
# (spec §4). A None value means the faction is solitary and never scouts or is
# scouted (ogre / minotaur / owlbear). A broken tribe with no listed rival
# simply leaves its lair empty for the halt window.
DESIGNATED_RIVAL: dict[str, str | None] = {
    "kobold": "orc_vol",
    "orc_vol": "orc_dec",
    "orc_dec": "orc_vol",
    "goblin": "gnoll",
    "gnoll": "goblin",
    "hobgoblin": "goblin",
    "bugbear": "hobgoblin",
    "ogre": None,
    "minotaur": None,
    "owlbear": None,
}

# Full Shrine of Evil Chaos reset cycle. 24 real hours (spec §1 SHRINE_RESET /
# §5). The Shrine is not tribe-scoped; it resets wholesale on this cadence.
SHRINE_RESET: int = 24 * 60 * 60

# Server-wide broadcast fired when the Shrine resets (spec §5). Content knob.
SHRINE_RESET_BROADCAST: str = "The cult regroups in the deep places."
