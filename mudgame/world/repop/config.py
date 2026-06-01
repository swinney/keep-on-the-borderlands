"""Repop tuning constants (R3 / docs/specs/repop.md §1).

Single tuning file for the wall-clock timing of tribe-scoped respawn. Only the
constants needed for standard respawn live here today; the leadership-halt,
rival-scouting, and Shrine-reset constants and the designated-rival table are
added by the later M6 tasks that implement those behaviors.

All durations are real-world seconds (wall-clock), not game time
(docs/architecture.md §5.2).
"""

from __future__ import annotations

# Normal mob respawn delay. 15 real minutes (spec §1 STANDARD_RESPAWN).
STANDARD_RESPAWN: int = 15 * 60

# How often the repop_manager reconciles due spawns (spec §1 MANAGER_TICK).
MANAGER_TICK: int = 60
