"""RepopManager GlobalScript: owns wall-clock respawn timers (R3 §6).

Pure repop logic lives in world.repop.state.RepopState; this script is the
long-lived Evennia owner that persists the spawn-point registry and the
per-point respawn timers across restarts, and fires the reconciliation tick.

Typeclasses report a mob death by calling ``notify_death(spawn_id)``; on each
``MANAGER_TICK`` the manager re-instantiates every point whose timer has
elapsed. The actual mob instantiation is delegated to ``world.build.spawner``
(world-build spec §6): the manager owns *when* to spawn (timers, halt windows,
the Shrine cycle), the spawner owns *how*. A spawn whose room is not yet built
returns ``None`` and the timer is still cleared, so the registry never wedges.

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
from evennia.utils import search

from world.build import spawner
from world.factions import config as fac_cfg
from world.repop import config as cfg
from world.repop.state import HaltEvent, RepopState, Scout, SpawnPoint
from world.zones.records import MobRecord, SpawnRecord
from world.zones.spawn_registry import spawn_points


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
        #   shrine_reset_at: epoch second the Shrine next resets (§5)
        self.db.points = {}
        self.db.respawn_at = {}
        self.db.halted_until = {}
        self.db.scouts = {}
        self.db.shrine_reset_at = None

    # ── State (de)serialization ──────────────────────────────────────────────

    def _repop_state(self) -> RepopState:
        state = RepopState()
        for fields in (self.db.points or {}).values():
            state.register(SpawnPoint(**fields))
        state.load_timers(dict(self.db.respawn_at or {}))
        state.load_halts(dict(self.db.halted_until or {}))
        state.load_scouts({sid: Scout(**fields) for sid, fields in (self.db.scouts or {}).items()})
        state.load_shrine(self.db.shrine_reset_at)
        return state

    def _save(self, state: RepopState) -> None:
        self.db.points = {p.spawn_id: asdict(p) for p in state.spawn_points()}
        self.db.respawn_at = state.pending_timers()
        self.db.halted_until = state.halt_windows()
        self.db.scouts = {sid: asdict(s) for sid, s in state.scout_records().items()}
        self.db.shrine_reset_at = state.shrine_window()

    # ── Registration API ──────────────────────────────────────────────────────

    def register(self, point: SpawnPoint) -> None:
        state = self._repop_state()
        state.register(point)
        self._save(state)

    def register_all(self, points: list[SpawnPoint]) -> None:
        state = self._repop_state()
        for point in points:
            state.register(point)
        self._save(state)

    def register_zone(
        self,
        zone: str,
        spawns: list[SpawnRecord],
        mob_templates: list[MobRecord],
    ) -> None:
        """Register a zone's static spawn data as live spawn points (R3 §1).

        Wires a zone's ``SPAWNS`` (incl. its ``chief``/``shaman`` leaders) into
        the manager so death reporting can fire the leadership halt + rival
        scouting (repop.md §3-4). Idempotent: re-registering a point marks it
        alive again, so a season-reset rebuild re-runs this safely.
        """
        self.register_all(spawn_points(zone, spawns, mob_templates))

    def populate(self) -> int:
        """Materialise one live mob per registered spawn point (world-build §4.4).

        The initial population pass the boot orchestrator runs after every zone's
        spawns are registered. Delegates each materialisation to the spawner,
        which is idempotent (skips a point that already has a live instance) and
        room-deferred (a not-yet-built room yields no mob), so this is safe to
        re-run on every boot and from the season rebuild. Returns the number of
        registered points that now stand as a live mob.
        """
        state = self._repop_state()
        count = 0
        for point in state.spawn_points():
            if spawner.spawn_mob(point) is not None:
                count += 1
        return count

    # ── Death / respawn API ───────────────────────────────────────────────────

    def notify_death(self, spawn_id: str, now: float | None = None) -> None:
        """Schedule a respawn for the point; act on any leadership halt (§3)."""
        state = self._repop_state()
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
        state = self._repop_state()
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

    def _tick_shrine(self, state: RepopState, now: float) -> None:
        """Advance the Shrine's 24h reset cycle (spec §5).

        Arms the cycle on first run; thereafter, each time a 24h boundary has
        elapsed it resets the Shrine — wholesale restock plus a server-wide
        broadcast — and re-arms the next cycle. Re-arming via mark_shrine_reset
        makes the reset idempotent within a window.
        """
        if state.shrine_reset_at() is None:
            state.schedule_shrine_reset(now)
            return
        if state.shrine_reset_due(now):
            self._reset_shrine(state)
            state.mark_shrine_reset(now)

    def _reset_shrine(self, state: RepopState) -> None:
        """Reset the Shrine wholesale and announce it server-wide (spec §5).

        The cult does not trickle back on per-mob timers: every Shrine spawn
        point is marked alive again at the 24h boundary (``restock``) and each is
        re-instantiated through the spawner, then the canonical server-wide
        broadcast fires. Registered Shrine points only exist once the zone has
        been registered (world build / season rebuild); with none registered the
        restock spawns nothing and only the broadcast fires, preserving prior
        behaviour.
        """
        for spawn_id in state.restock(cfg.SHRINE_ZONE):
            self._instantiate(state.get(spawn_id))
        self._broadcast(cfg.SHRINE_RESET_BROADCAST)

    # ── Season-reset hooks (R6 §3.3; called by the season_manager) ────────────

    def reset_season(self, now: float | None = None) -> None:
        """Clear all repop timers, halts, and scouts; re-arm the Shrine cycle.

        The static spawn-point registry is retained; the season_manager's world
        rebuild re-instantiates the live mobs from it.
        """
        state = self._repop_state()
        state.reset_season(now if now is not None else time.time())
        self._save(state)

    def reset_shrine(self, now: float | None = None) -> None:
        """Restock the Shrine and re-arm its 24h cycle at season start (R6 §3.3).

        Re-instantiating the Shrine's boss and rooms lands with the Shrine zone
        (M11); until then this re-arms the timer, mirroring how ``_instantiate``
        stands in for real spawning.
        """
        state = self._repop_state()
        state.schedule_shrine_reset(now if now is not None else time.time())
        self._save(state)

    def at_repeat(self) -> None:
        """Reconcile the Shrine cycle, due spawns, and scout retreats per tick."""
        state = self._repop_state()
        now = time.time()
        self._tick_shrine(state, now)
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
        """Re-instantiate a mob from its template at its room (world-build §6).

        Delegates the materialisation to ``world.build.spawner``; the caller still
        clears the timer regardless, so a missing room/template (spawner returns
        ``None``) never wedges the registry.
        """
        spawner.spawn_mob(point)

    def _instantiate_scout(self, scout: Scout) -> None:
        """Instantiate a rival scout in a broken tribe's lair (§4; world-build §6)."""
        spawner.spawn_scout(scout)

    def _retreat_scout(self, scout: Scout) -> None:
        """Despawn a scout that retreats as the original tribe regroups (§4)."""
        spawner.despawn(scout.scout_id)

    # Satisfy mypy: Evennia base attributes accessed dynamically.
    db: Any
