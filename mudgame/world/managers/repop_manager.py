"""RepopManager GlobalScript: owns wall-clock respawn timers (R3 §6).

Pure repop logic lives in world.repop.state.RepopState; this script is the
long-lived Evennia owner that persists the spawn-point registry and the
per-point respawn timers across restarts, and fires the reconciliation tick.

Typeclasses report a mob death by calling ``notify_death(spawn_id)``; on each
``MANAGER_TICK`` the manager re-instantiates every point whose timer has
elapsed. The actual mob instantiation is delegated to ``_instantiate`` and is
wired to real zone prototypes by the zone milestones (M7/M9); until those exist
it is a safe no-op that still clears the timer so the registry stays consistent.

Usage (from anywhere in the running game)::

    from evennia.utils import search
    mgr = search.search_script("repop_manager")[0]
    mgr.notify_death("kobold_warren_guard_1")
"""

from __future__ import annotations

import time
from dataclasses import asdict
from typing import Any

from evennia.scripts.scripts import DefaultScript
from evennia.utils import logger

from world.repop import config as cfg
from world.repop.state import RepopState, SpawnPoint


class RepopManager(DefaultScript):
    """Global script owning spawn-point registration and respawn timers."""

    def at_script_creation(self) -> None:
        self.key = "repop_manager"
        self.desc = "Owns tribe-scoped spawn points and wall-clock respawn timers."
        self.interval = cfg.MANAGER_TICK
        self.persistent = True
        self.start_delay = True
        # Persisted as plain dicts so Evennia Attributes can store them:
        #   points:     spawn_id -> SpawnPoint field dict
        #   respawn_at: spawn_id -> epoch second the point is due to respawn
        self.db.points = {}
        self.db.respawn_at = {}

    # ── State (de)serialization ──────────────────────────────────────────────

    def _state(self) -> RepopState:
        state = RepopState()
        for fields in (self.db.points or {}).values():
            state.register(SpawnPoint(**fields))
        state.load_timers(dict(self.db.respawn_at or {}))
        return state

    def _save(self, state: RepopState) -> None:
        self.db.points = {p.spawn_id: asdict(p) for p in state.spawn_points()}
        self.db.respawn_at = state.pending_timers()

    # ── Registration API ──────────────────────────────────────────────────────

    def register(self, point: SpawnPoint) -> None:
        state = self._state()
        state.register(point)
        self._save(state)

    def register_all(self, points: list[SpawnPoint]) -> None:
        state = self._state()
        for point in points:
            state.register(point)
        self._save(state)

    # ── Death / respawn API ───────────────────────────────────────────────────

    def notify_death(self, spawn_id: str, now: float | None = None) -> None:
        """Schedule a respawn for the point at the next due tick."""
        state = self._state()
        state.notify_death(spawn_id, now if now is not None else time.time())
        self._save(state)

    def at_repeat(self) -> None:
        """Reconcile due spawns once per MANAGER_TICK."""
        state = self._state()
        for spawn_id in state.due_spawns(time.time()):
            self._instantiate(state.get(spawn_id))
            state.mark_respawned(spawn_id)
        self._save(state)

    def _instantiate(self, point: SpawnPoint) -> None:
        """Re-instantiate a mob from its template at its room.

        Wired to real zone prototypes by M7/M9. Until those zones exist this is
        a logged no-op; the caller still clears the timer so the registry does
        not wedge on missing templates.
        """
        logger.log_info(f"repop_manager: respawn due for {point.spawn_id} ({point.mob_template})")

    # Satisfy mypy: Evennia base attributes accessed dynamically.
    db: Any
