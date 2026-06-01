"""Pure-Python seasonal-reset orchestration (R6 / docs/specs/seasonal-reset.md).

No Evennia imports — fully unit-testable. ``SeasonState`` owns the season counter
and timing (length, end, pre-boundary warnings); ``run_reset`` performs the
deterministic reset sequence (spec §3) by calling injected manager reset hooks,
so the whole orchestration is testable without booting the server.

The season_manager GlobalScript supplies the real clock, implements ``ResetHooks``
by delegating to the other GlobalScripts, and persists this state.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Protocol

from world.season import config as _cfg
from world.season.leaderboard import Leaderboard, Survivor


class ResetHooks(Protocol):
    """Side-effecting reset steps ``run_reset`` delegates to the manager (spec §3).

    Each method maps to a world manager (or zone) the season_manager flushes; the
    pure orchestration only fixes the *order* in which they fire, never their
    logic. Player characters are deliberately absent — they are never touched.
    """

    def reset_factions(self) -> None: ...
    def reset_repop(self) -> None: ...
    def reset_priest(self) -> None: ...
    def reset_shrine(self) -> None: ...
    def revert_season_quests(self) -> None: ...
    def rebuild_world(self) -> None: ...
    def refresh_roster(self) -> None: ...


@dataclass(frozen=True)
class ResetReport:
    """Summary of a completed reset, returned to the manager and tests."""

    closing_season: int
    new_season: int
    new_start: float
    reason: str | None
    survivors_recorded: int


@dataclass
class SeasonState:
    """Season counter plus timing; the manager persists these fields.

    ``warned`` tracks which pre-boundary warning offsets have already fired this
    season so a warning never repeats; it clears when the season advances.
    """

    season_number: int = 1
    season_start: float = 0.0
    length_seconds: int = _cfg.SEASON_LENGTH
    warned: set[int] = field(default_factory=set)

    def season_end(self) -> float:
        """Epoch second the current season is due to end (spec §1)."""
        return self.season_start + self.length_seconds

    def is_expired(self, now: float) -> bool:
        """True once the timed season boundary has been reached."""
        return now >= self.season_end()

    def due_warnings(self, now: float) -> tuple[int, ...]:
        """Warning offsets whose pre-boundary time has passed and not yet fired.

        Returned longest-offset-first (T-24h before T-1h) for a deterministic
        broadcast order; the manager calls ``mark_warned`` as it delivers each.
        """
        end = self.season_end()
        return tuple(
            offset
            for offset in _cfg.WARN_OFFSETS
            if now >= end - offset and offset not in self.warned
        )

    def mark_warned(self, offset: int) -> None:
        """Record that a warning offset has fired so it does not repeat."""
        self.warned.add(offset)

    def advance(self, now: float) -> None:
        """Open the next season: bump the counter, restart the clock, clear warnings."""
        self.season_number += 1
        self.season_start = now
        self.warned = set()


def run_reset(
    state: SeasonState,
    leaderboard: Leaderboard,
    hooks: ResetHooks,
    survivors: Sequence[Survivor],
    now: float,
    reason: str | None = None,
) -> ResetReport:
    """Run the deterministic season-reset sequence (spec §3 / §5).

    Order matters and is asserted by tests:
      1. Snapshot the closing season's survivors *before* anything advances
         (§3.2) — they are stamped with the still-current season number.
      2. Flush the world managers: factions, repop, priest, Shrine (§3.3).
      3. Revert season-global quest effects, e.g. a destroyed Shrine (§3.4).
      4. Rebuild live instances and refresh the henchmen roster (§3.5).
      5. Advance the season counter and restart the clock (§3.6).

    Broadcasts (§3.1 warnings, §3.7 new-season, §5 early-end framing) are side
    effects the manager performs around this call. Player characters are never
    touched.
    """
    closing = state.season_number
    snapped = leaderboard.snapshot_survivors(closing, survivors, now)

    hooks.reset_factions()
    hooks.reset_repop()
    hooks.reset_priest()
    hooks.reset_shrine()
    hooks.revert_season_quests()
    hooks.rebuild_world()
    hooks.refresh_roster()

    state.advance(now)
    return ResetReport(
        closing_season=closing,
        new_season=state.season_number,
        new_start=now,
        reason=reason,
        survivors_recorded=len(snapped),
    )
