"""Tribe-scoped repop core (R3 / docs/specs/repop.md).

Pure-Python spawn-point registry and respawn-timer logic, free of Evennia
imports so it is unit-testable without booting the server. The repop_manager
GlobalScript (world/managers/repop_manager.py) wraps this and owns the
wall-clock timers.
"""
