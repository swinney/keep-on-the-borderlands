"""Seasonal-reset tuning constants (R6 / docs/specs/seasonal-reset.md §1, §3).

Single tuning file for the campaign-season cadence: its length, the pre-boundary
warning offsets, and the broadcast copy. All durations are real-world seconds
(wall-clock), not game time (docs/architecture.md §5.2).
"""

from __future__ import annotations

# Default campaign-season length: 6 weeks (spec §1). Tunable so operators can run
# faster test seasons or longer live ones; the season_manager reads it per-state.
SEASON_LENGTH: int = 42 * 24 * 60 * 60

# How often the season_manager checks the clock for due warnings / expiry.
MANAGER_TICK: int = 60

# Offsets *before* season end at which a fade warning broadcasts (spec §3.1).
# Listed longest-first so the T-24h warning precedes the T-1h one.
WARN_OFFSETS: tuple[int, ...] = (24 * 60 * 60, 60 * 60)

# Per-offset broadcast copy ("the season wanes…", spec §3.1). Content knob.
WANE_BROADCASTS: dict[int, str] = {
    24 * 60 * 60: "The season wanes over the Borderlands; one day remains.",
    60 * 60: "The season is all but spent; one hour remains before the world is remade.",
}

# Broadcast after a reset opens a fresh season (spec §3.7). Content knob.
NEW_SEASON_BROADCAST: str = (
    "A new season dawns over the Borderlands; the Caves stir with fresh menace."
)

# Bespoke framing for an early end via end_season (spec §5). The canonical case
# is the Shrine's destruction; the trigger supplies the machine reason separately.
EARLY_END_BROADCAST: str = "The Shrine lies in ruins; the season ends in triumph."
