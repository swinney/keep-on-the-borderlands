"""PriestManager GlobalScript: owns the disguised priest's seasonal identity (R4).

Pure rotation logic lives in world.priest.state.PriestState; this script is the
long-lived Evennia owner that persists the current/previous spy across restarts
and re-rolls the identity at each season boundary.

The season_manager's ``reset_priest`` hook calls ``reset_season`` once per season
(R6 §3.3); the manager re-rolls the spy, never picking the NPC that just served
(spec §2). Clue assignment, detection paths, the quest chain, and exposure land
with the later M12 slices and extend this manager.

Usage (from anywhere in the running game)::

    from evennia.utils import search
    mgr = search.search_script("priest_manager")[0]
    mgr.spy_id            # current season's disguised priest
"""

from __future__ import annotations

from random import Random
from typing import Any

from evennia.scripts.scripts import DefaultScript
from evennia.utils import logger

from world.priest.state import PriestState


class PriestManager(DefaultScript):
    """Global script owning the rotating disguised-priest identity."""

    def at_script_creation(self) -> None:
        self.key = "priest_manager"
        self.desc = "Owns the disguised priest's rotating seasonal identity."
        self.persistent = True
        # Persisted plainly so Evennia Attributes can store it:
        #   spy_id — the current season's spy NPC id (None before first roll)
        self.db.spy_id = None
        # Seed the first season's identity immediately so the chapel always has
        # a spy from creation onward.
        self.assign_spy()

    # ── State (de)serialization ───────────────────────────────────────────────

    def _priest_state(self) -> PriestState:
        return PriestState(spy_id=self.db.spy_id)

    def _save(self, state: PriestState) -> None:
        self.db.spy_id = state.spy_id

    # ── Identity API ──────────────────────────────────────────────────────────

    @property
    def spy_id(self) -> str | None:
        """The current season's disguised-priest NPC id."""
        return self.db.spy_id

    def assign_spy(self, rng: Random | None = None) -> str:
        """Roll this season's spy, never repeating the outgoing one (spec §2).

        ``rng`` is injectable for deterministic tests; production passes a fresh
        ``Random`` so the seasonal pick is unpredictable.
        """
        state = self._priest_state()
        spy_id = state.assign_spy(rng if rng is not None else Random())
        self._save(state)
        logger.log_info(f"priest_manager: disguised priest is now {spy_id}.")
        return spy_id

    # ── Season-reset hook (R6 §3.3; called by the season_manager) ─────────────

    def reset_season(self, rng: Random | None = None) -> None:
        """Re-roll the spy at the season boundary, excluding the outgoing one."""
        self.assign_spy(rng)

    # Satisfy mypy: Evennia base attributes accessed dynamically.
    db: Any
