"""Pure-Python repop state: spawn-point registry and standard respawn timers.

No Evennia imports — fully unit-testable without booting the server. The
repop_manager GlobalScript wraps this class, persists the timer dict via
Evennia Attributes, reports mob deaths into it, and reconciles due spawns on
each MANAGER_TICK.

Wall-clock time is passed in explicitly (epoch seconds) rather than read from a
clock here, so every transition is deterministic under test; the manager
supplies the real clock (docs/specs/repop.md §1, §2).

This module implements M6 Task 1 (registration + standard respawn), Task 2
(leadership halt, §3), Task 3 (rival scouting, §4), and Task 4 (the Shrine
reset cycle, §5). Seasonal reset (§6) is layered on by a later task.
"""

from __future__ import annotations

from dataclasses import dataclass

from world.repop import config as _cfg


@dataclass(frozen=True)
class HaltEvent:
    """Signal returned by ``notify_death`` when a leadership halt triggers (§3).

    The pure core cannot perform side effects (zone broadcast, faction tension,
    rival scouting); it names the broken tribe and the window end so the
    repop_manager can carry them out.

    faction       tribe whose chief and shaman are both dead.
    halted_until  epoch second the repop freeze lifts (now + LEADERSHIP_HALT).
    rival         designated rival that scouts the empty lair (§4), or None for
                  a solitary/rival-less tribe. The scouts themselves are already
                  recorded in RepopState (see scouts_for); this names the side.
    """

    faction: str
    halted_until: float
    rival: str | None = None


@dataclass(frozen=True)
class Scout:
    """A rival mob occupying a halted tribe's lair (spec §4).

    scout_id   unique key for this scout within the world.
    faction    the designated rival's faction id — scouts count as the rival
               for all R2 purposes, never as the broken tribe.
    room       a lair room of the broken tribe where the scout appears.
    scouting   the broken tribe whose halt window this scout occupies; when that
               halt expires the scout retreats (despawns).
    """

    scout_id: str
    faction: str
    room: str
    scouting: str


@dataclass(frozen=True)
class SpawnPoint:
    """A static spawn definition drawn from zone data (spec §1).

    spawn_id        unique key for this point within the world.
    room            identifier of the room where the mob (re)appears.
    mob_template    prototype/template name to instantiate.
    faction         faction id of the template; also its tribe id (R2).
    respawn_seconds per-point delay; defaults to STANDARD_RESPAWN.
    is_leader       True for the chief/shaman points (used by §3, later task).
    leader_role     "chief" | "shaman" | None.
    """

    spawn_id: str
    room: str
    mob_template: str
    faction: str
    respawn_seconds: int = _cfg.STANDARD_RESPAWN
    is_leader: bool = False
    leader_role: str | None = None


class RepopState:
    """Owns the spawn-point registry and per-point respawn timers.

    A registered point is "alive" (populated) by default. On death the manager
    calls notify_death, scheduling respawn_at = now + respawn_seconds. due_spawns
    reports points whose timer has elapsed; the manager re-instantiates each and
    calls mark_respawned to clear the timer.
    """

    def __init__(self) -> None:
        self._points: dict[str, SpawnPoint] = {}
        # spawn_id -> epoch seconds at which the point is due to respawn.
        # A spawn_id absent from this map is currently alive (no pending timer).
        self._respawn_at: dict[str, float] = {}
        # faction -> epoch second a leadership halt lifts (spec §3). While the
        # value is in the future, nothing in that tribe repops.
        self._halted_until: dict[str, float] = {}
        # scout_id -> Scout currently occupying a halted lair (spec §4).
        self._scouts: dict[str, Scout] = {}
        # Epoch second the Shrine is next due to reset (spec §5), or None until
        # the cycle is armed at world build / season start. The Shrine is not
        # tribe-scoped; it resets wholesale on the SHRINE_RESET cadence.
        self._shrine_reset_at: float | None = None

    # ── Registration ────────────────────────────────────────────────────────

    def register(self, point: SpawnPoint) -> None:
        """Register (or re-register) a spawn point as currently alive."""
        self._points[point.spawn_id] = point
        self._respawn_at.pop(point.spawn_id, None)

    def spawn_points(self) -> tuple[SpawnPoint, ...]:
        """All registered spawn points (insertion order)."""
        return tuple(self._points.values())

    def get(self, spawn_id: str) -> SpawnPoint:
        """The registered point for spawn_id (raises KeyError if unknown)."""
        return self._points[spawn_id]

    def is_registered(self, spawn_id: str) -> bool:
        return spawn_id in self._points

    # ── Respawn timers ──────────────────────────────────────────────────────

    def is_pending(self, spawn_id: str) -> bool:
        """True when the point is dead and awaiting respawn."""
        return spawn_id in self._respawn_at

    def respawn_at(self, spawn_id: str) -> float | None:
        """Epoch second the point is due to respawn, or None if alive."""
        return self._respawn_at.get(spawn_id)

    def notify_death(self, spawn_id: str, now: float) -> HaltEvent | None:
        """Record a mob death and schedule its respawn (spec §2, §3).

        Schedules ``respawn_at = now + respawn_seconds`` for the point. Leaders
        respawn on the same standard timer individually; but if the dying mob is
        a leader and its tribe's *other* leader is already dead, both leaders are
        down at once → a leadership halt triggers (§3) and a HaltEvent is
        returned for the manager to act on. Otherwise returns None.
        """
        point = self._points[spawn_id]
        self._respawn_at[spawn_id] = now + point.respawn_seconds

        if point.is_leader:
            other = self._other_leader(point.faction, point.leader_role)
            if other is not None and self.is_pending(other.spawn_id):
                return self._trigger_halt(point.faction, now)
        return None

    def due_spawns(self, now: float) -> tuple[str, ...]:
        """Pending spawn ids whose respawn timer has elapsed at `now`.

        A point belonging to a currently-halted tribe is never due — during a
        leadership halt nothing in that tribe repops (§3). Returned sorted by
        spawn_id for deterministic reconciliation order.
        """
        return tuple(
            sorted(
                sid
                for sid, at in self._respawn_at.items()
                if at <= now and not self.is_halted(self._points[sid].faction, now)
            )
        )

    def mark_respawned(self, spawn_id: str) -> None:
        """Clear the pending timer once the manager has re-instantiated a point."""
        self._respawn_at.pop(spawn_id, None)

    def restock(self, zone: str) -> tuple[str, ...]:
        """Revive every *dead* spawn point in ``zone`` at once (wholesale restock, §5).

        The Shrine's 24h reset brings the cult back together rather than via
        per-mob timers. Only points that are currently pending (dead) under the
        ``"<zone>:..."`` namespace are revived: their respawn timer is cleared
        and their id returned (sorted) for the manager to re-instantiate, exactly
        like ``due_spawns``. Already-alive points are left untouched, so a future
        live spawner re-creates only what is actually missing — never a duplicate.
        """
        prefix = f"{zone}:"
        restocked = tuple(
            sorted(sid for sid in self._points if sid.startswith(prefix) and self.is_pending(sid))
        )
        for spawn_id in restocked:
            self._respawn_at.pop(spawn_id, None)
        return restocked

    # ── Leadership halt (spec §3) ─────────────────────────────────────────────

    def _other_leader(self, faction: str, role: str | None) -> SpawnPoint | None:
        """The tribe's other designated leader point (chief↔shaman), if any."""
        for candidate in self._points.values():
            if (
                candidate.faction == faction
                and candidate.is_leader
                and candidate.leader_role != role
            ):
                return candidate
        return None

    def _trigger_halt(self, faction: str, now: float) -> HaltEvent:
        """Freeze the tribe's repop for LEADERSHIP_HALT and mark it for regroup.

        Every spawn point in the tribe is scheduled to come due exactly when the
        window lifts, so the *entire* tribe regroups with fresh leaders at the
        first tick after expiry (§3).
        """
        halted_until = now + _cfg.LEADERSHIP_HALT
        self._halted_until[faction] = halted_until
        for candidate in self._points.values():
            if candidate.faction == faction:
                self._respawn_at[candidate.spawn_id] = halted_until
        rival = self._spawn_scouts(faction)
        return HaltEvent(faction=faction, halted_until=halted_until, rival=rival)

    # ── Rival scouting (spec §4) ──────────────────────────────────────────────

    def _spawn_scouts(self, faction: str) -> str | None:
        """Move a designated rival's scouting party into the broken tribe's lair.

        Spawns SCOUT_PARTY_SIZE scouts of the rival faction, distributed across
        the broken tribe's lair rooms. Returns the rival faction id, or None when
        the tribe has no designated rival (solitary) or no known lair rooms.
        """
        rival = _cfg.DESIGNATED_RIVAL.get(faction)
        if rival is None:
            return None
        rooms = sorted({p.room for p in self._points.values() if p.faction == faction})
        if not rooms:
            return None
        for i in range(_cfg.SCOUT_PARTY_SIZE):
            scout_id = f"{rival}_scout_{faction}_{i}"
            self._scouts[scout_id] = Scout(
                scout_id=scout_id,
                faction=rival,
                room=rooms[i % len(rooms)],
                scouting=faction,
            )
        return rival

    def active_scouts(self) -> tuple[Scout, ...]:
        """All scouts currently in the world, sorted by scout_id."""
        return tuple(self._scouts[sid] for sid in sorted(self._scouts))

    def scouts_for(self, faction: str) -> tuple[Scout, ...]:
        """Scouts currently occupying the named broken tribe's lair."""
        return tuple(s for s in self.active_scouts() if s.scouting == faction)

    def get_scout(self, scout_id: str) -> Scout:
        """The scout for scout_id (raises KeyError if unknown)."""
        return self._scouts[scout_id]

    def notify_scout_death(self, scout_id: str) -> None:
        """Remove a scout a player has killed (it does not respawn; §4)."""
        self._scouts.pop(scout_id, None)

    def due_scout_retreats(self, now: float) -> tuple[str, ...]:
        """Scout ids whose broken tribe is no longer halted at `now`.

        On halt expiry surviving scouts retreat as the tribe regroups (§4); the
        manager despawns each and calls mark_scout_retreated. Sorted for a
        deterministic reconciliation order.
        """
        return tuple(
            sorted(
                sid
                for sid, scout in self._scouts.items()
                if not self.is_halted(scout.scouting, now)
            )
        )

    def mark_scout_retreated(self, scout_id: str) -> None:
        """Clear a scout once the manager has despawned it on regroup."""
        self._scouts.pop(scout_id, None)

    def is_halted(self, faction: str, now: float) -> bool:
        """True while the tribe's leadership-halt window is still in the future."""
        until = self._halted_until.get(faction)
        return until is not None and until > now

    def halted_until(self, faction: str) -> float | None:
        """Epoch second the tribe's halt lifts, or None if it was never halted."""
        return self._halted_until.get(faction)

    # ── Shrine reset (spec §5) ────────────────────────────────────────────────

    def schedule_shrine_reset(self, now: float) -> None:
        """Arm the Shrine's 24h reset cycle, starting from ``now`` (spec §5)."""
        self._shrine_reset_at = now + _cfg.SHRINE_RESET

    def shrine_reset_at(self) -> float | None:
        """Epoch second the Shrine is next due to reset, or None if unarmed."""
        return self._shrine_reset_at

    def shrine_reset_due(self, now: float) -> bool:
        """True once the Shrine's 24h cycle has elapsed and a reset is due (§5)."""
        return self._shrine_reset_at is not None and now >= self._shrine_reset_at

    def mark_shrine_reset(self, now: float) -> None:
        """Re-arm the next cycle once the manager has performed the reset (§5).

        Advancing by whole SHRINE_RESET periods (not ``now + SHRINE_RESET``)
        keeps a fixed cadence and makes the reset idempotent within a window:
        re-checking before the next boundary never re-fires. Whole cycles missed
        while the server was down are skipped so the timer never lags forever.
        """
        base = self._shrine_reset_at if self._shrine_reset_at is not None else now
        nxt = base + _cfg.SHRINE_RESET
        while nxt <= now:
            nxt += _cfg.SHRINE_RESET
        self._shrine_reset_at = nxt

    # ── Season reset (docs/specs/seasonal-reset.md §3.3) ──────────────────────

    def reset_season(self, now: float) -> None:
        """Clear every live repop timer, halt, and scout; re-arm the Shrine cycle.

        Season reset wipes the repop domain's wall-clock state so every
        registered spawn point is alive again and no tribe is frozen, then arms a
        fresh 24h Shrine cycle from ``now``. The static spawn-point registry (zone
        data) is retained — the manager rebuilds the live mob instances from it.
        """
        self._respawn_at = {}
        self._halted_until = {}
        self._scouts = {}
        self.schedule_shrine_reset(now)

    # ── Persistence helpers (used by the manager) ─────────────────────────────

    def pending_timers(self) -> dict[str, float]:
        """A copy of the absolute respawn timers, for the manager to persist."""
        return dict(self._respawn_at)

    def load_timers(self, respawn_at: dict[str, float]) -> None:
        """Restore persisted absolute respawn timers after a reload."""
        self._respawn_at = dict(respawn_at)

    def halt_windows(self) -> dict[str, float]:
        """A copy of the per-tribe halt end-times, for the manager to persist."""
        return dict(self._halted_until)

    def load_halts(self, halted_until: dict[str, float]) -> None:
        """Restore persisted per-tribe halt windows after a reload."""
        self._halted_until = dict(halted_until)

    def scout_records(self) -> dict[str, Scout]:
        """A copy of the active scouts, for the manager to persist."""
        return dict(self._scouts)

    def load_scouts(self, scouts: dict[str, Scout]) -> None:
        """Restore persisted scouts after a reload."""
        self._scouts = dict(scouts)

    def shrine_window(self) -> float | None:
        """The Shrine's next-reset epoch second, for the manager to persist."""
        return self._shrine_reset_at

    def load_shrine(self, shrine_reset_at: float | None) -> None:
        """Restore the persisted Shrine reset window after a reload."""
        self._shrine_reset_at = shrine_reset_at
