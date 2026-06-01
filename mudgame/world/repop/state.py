"""Pure-Python repop state: spawn-point registry and standard respawn timers.

No Evennia imports — fully unit-testable without booting the server. The
repop_manager GlobalScript wraps this class, persists the timer dict via
Evennia Attributes, reports mob deaths into it, and reconciles due spawns on
each MANAGER_TICK.

Wall-clock time is passed in explicitly (epoch seconds) rather than read from a
clock here, so every transition is deterministic under test; the manager
supplies the real clock (docs/specs/repop.md §1, §2).

This module implements M6 Task 1 — registration + standard respawn. Leadership
halt (§3), rival scouting (§4), and Shrine reset (§5) are layered on by later
tasks; their hooks are intentionally absent until then.
"""

from __future__ import annotations

from dataclasses import dataclass

from world.repop import config as _cfg


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

    def notify_death(self, spawn_id: str, now: float) -> None:
        """Record a mob death: schedule respawn_at = now + its respawn delay."""
        point = self._points[spawn_id]
        self._respawn_at[spawn_id] = now + point.respawn_seconds

    def due_spawns(self, now: float) -> tuple[str, ...]:
        """Pending spawn ids whose respawn timer has elapsed at `now`.

        Returned sorted by spawn_id for deterministic reconciliation order.
        """
        return tuple(sorted(sid for sid, at in self._respawn_at.items() if at <= now))

    def mark_respawned(self, spawn_id: str) -> None:
        """Clear the pending timer once the manager has re-instantiated a point."""
        self._respawn_at.pop(spawn_id, None)

    # ── Persistence helpers (used by the manager) ─────────────────────────────

    def pending_timers(self) -> dict[str, float]:
        """A copy of the absolute respawn timers, for the manager to persist."""
        return dict(self._respawn_at)

    def load_timers(self, respawn_at: dict[str, float]) -> None:
        """Restore persisted absolute respawn timers after a reload."""
        self._respawn_at = dict(respawn_at)
