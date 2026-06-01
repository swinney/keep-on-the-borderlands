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

import evennia
from evennia.scripts.scripts import DefaultScript
from evennia.utils import logger, search

from world.factions import config as fac_cfg
from world.repop import config as cfg
from world.repop.state import HaltEvent, RepopState, Scout, SpawnPoint


class RepopManager(DefaultScript):
    """Global script owning spawn-point registration and respawn timers."""

    def at_script_creation(self) -> None:
        self.key = "repop_manager"
        self.desc = "Owns tribe-scoped spawn points and wall-clock respawn timers."
        self.interval = cfg.MANAGER_TICK
        self.persistent = True
        self.start_delay = True
        # Persisted as plain dicts so Evennia Attributes can store them:
        #   points:       spawn_id -> SpawnPoint field dict
        #   respawn_at:   spawn_id -> epoch second the point is due to respawn
        #   halted_until: faction -> epoch second a leadership halt lifts (§3)
        #   scouts:       scout_id -> Scout field dict (rival scouting, §4)
        self.db.points = {}
        self.db.respawn_at = {}
        self.db.halted_until = {}
        self.db.scouts = {}

    # ── State (de)serialization ──────────────────────────────────────────────

    def _state(self) -> RepopState:
        state = RepopState()
        for fields in (self.db.points or {}).values():
            state.register(SpawnPoint(**fields))
        state.load_timers(dict(self.db.respawn_at or {}))
        state.load_halts(dict(self.db.halted_until or {}))
        state.load_scouts({sid: Scout(**fields) for sid, fields in (self.db.scouts or {}).items()})
        return state

    def _save(self, state: RepopState) -> None:
        self.db.points = {p.spawn_id: asdict(p) for p in state.spawn_points()}
        self.db.respawn_at = state.pending_timers()
        self.db.halted_until = state.halt_windows()
        self.db.scouts = {sid: asdict(s) for sid, s in state.scout_records().items()}

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
        """Schedule a respawn for the point; act on any leadership halt (§3)."""
        state = self._state()
        event = state.notify_death(spawn_id, now if now is not None else time.time())
        self._save(state)
        if event is not None:
            self._on_leadership_halt(event, state)

    def _on_leadership_halt(self, event: HaltEvent, state: RepopState) -> None:
        """Carry out a triggered halt: broadcast + R2 leadership_broken + scouts.

        The pure core has already recorded the scouting party (§4) in `state`;
        here we deliver the §3 disarray broadcast, apply the R2 tension spike,
        and instantiate the rival scouts that moved into the empty lair.
        """
        tribe = self._tribe_display(event.faction)
        message = f"With chief and shaman both slain, {tribe} warren falls into disarray."
        self._broadcast(message)
        managers = search.search_script("faction_manager")
        if managers:
            managers[0].apply_leadership_broken(event.faction)
        for scout in state.scouts_for(event.faction):
            self._instantiate_scout(scout)

    def notify_scout_death(self, scout_id: str, player_key: str | None = None) -> None:
        """Record a player killing a rival scout (§4).

        The scout does not respawn. Standing shifts with the *rival* faction it
        belongs to, never the broken tribe whose lair it was occupying.
        """
        state = self._state()
        scout = state.scout_records().get(scout_id)
        state.notify_scout_death(scout_id)
        self._save(state)
        if scout is not None and player_key is not None:
            managers = search.search_script("faction_manager")
            if managers:
                managers[0].apply_kill_member(scout.faction, player_key)

    @staticmethod
    def _tribe_display(faction: str) -> str:
        """Human-readable tribe name for broadcasts, falling back to the id."""
        definition = fac_cfg.FACTIONS.get(faction)
        return definition["display"] if definition is not None else faction

    @staticmethod
    def _broadcast(message: str) -> None:
        """Announce to every connected session.

        Zone-scoped delivery awaits the zone room registry (M7+); until then a
        server-wide announcement is the safe analogue, mirroring _instantiate.
        """
        if evennia.SESSION_HANDLER is not None:
            for session in evennia.SESSION_HANDLER.get_sessions():
                session.msg(message)

    def at_repeat(self) -> None:
        """Reconcile due spawns and scout retreats once per MANAGER_TICK."""
        state = self._state()
        now = time.time()
        # Surviving scouts retreat the moment their tribe's halt lifts (§4),
        # before the tribe's own members regroup into the same rooms.
        for scout_id in state.due_scout_retreats(now):
            self._retreat_scout(state.get_scout(scout_id))
            state.mark_scout_retreated(scout_id)
        for spawn_id in state.due_spawns(now):
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

    def _instantiate_scout(self, scout: Scout) -> None:
        """Instantiate a rival scout in a broken tribe's lair (§4).

        Wired to real zone prototypes by M7/M9, mirroring ``_instantiate``;
        until then a logged no-op so the scout registry stays consistent.
        """
        logger.log_info(
            f"repop_manager: scout {scout.scout_id} ({scout.faction}) moves into {scout.room}"
        )

    def _retreat_scout(self, scout: Scout) -> None:
        """Despawn a scout that retreats as the original tribe regroups (§4)."""
        logger.log_info(f"repop_manager: scout {scout.scout_id} retreats from {scout.room}")

    # Satisfy mypy: Evennia base attributes accessed dynamically.
    db: Any
