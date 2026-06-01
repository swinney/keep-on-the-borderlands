"""Seasonal-reset subsystem (R6 / docs/specs/seasonal-reset.md).

Pure core (config, leaderboard, state + orchestration) lives here; the
season_manager GlobalScript (world/managers/season_manager.py) is the thin
Evennia wrapper that supplies the clock, the real reset hooks, and persistence.
"""
