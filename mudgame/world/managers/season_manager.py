"""SeasonManager GlobalScript: orchestrates the seasonal reset (R6 §3).

Pure season logic lives in world.season.state (timing + counter, the run_reset
sequence) and world.season.leaderboard (placements); this script is the
long-lived Evennia owner that supplies the wall-clock, persists both across
restarts, fires the pre-boundary warnings and the timed reset, and implements
``ResetHooks`` by delegating to the other world managers.

It deliberately never touches player Accounts/Characters — only world-owned
state resets (spec §2).

Usage (from anywhere in the running game)::

    from evennia.utils import search
    mgr = search.search_script("season_manager")[0]
    mgr.end_season(reason="shrine_destroyed")   # early end (spec §5)
"""

from __future__ import annotations

import time
from dataclasses import asdict
from typing import Any

import evennia
from evennia.scripts.scripts import DefaultScript
from evennia.server.models import ServerConfig
from evennia.utils import logger, search

from typeclasses.characters import Character
from world.season import config as cfg
from world.season.leaderboard import Leaderboard, LeaderboardEntry, Survivor
from world.season.state import ResetReport, SeasonState, run_reset


class SeasonManager(DefaultScript):
    """Global script owning the season clock, leaderboard, and reset sequence."""

    def at_script_creation(self) -> None:
        self.key = "season_manager"
        self.desc = "Orchestrates seasonal resets and owns the leaderboard."
        self.interval = cfg.MANAGER_TICK
        self.persistent = True
        self.start_delay = True
        # Persisted plainly so Evennia Attributes can store them:
        #   season_number / season_start / length_seconds — the SeasonState fields
        #   warned       — list of warning offsets already fired this season
        #   leaderboard  — list of LeaderboardEntry field dicts (append-only)
        self.db.season_number = 1
        self.db.season_start = time.time()
        self.db.length_seconds = cfg.SEASON_LENGTH
        self.db.warned = []
        self.db.leaderboard = []
        # Keep death.md's hardcore-death path in sync with the live season.
        self._publish_season_number(1)

    # ── State (de)serialization ───────────────────────────────────────────────

    def _season_state(self) -> SeasonState:
        return SeasonState(
            season_number=self.db.season_number,
            season_start=self.db.season_start,
            length_seconds=self.db.length_seconds or cfg.SEASON_LENGTH,
            warned=set(self.db.warned or []),
        )

    def _save_season(self, state: SeasonState) -> None:
        self.db.season_number = state.season_number
        self.db.season_start = state.season_start
        self.db.length_seconds = state.length_seconds
        self.db.warned = sorted(state.warned)
        self._publish_season_number(state.season_number)

    def _leaderboard(self) -> Leaderboard:
        entries = [LeaderboardEntry(**fields) for fields in (self.db.leaderboard or [])]
        return Leaderboard(entries)

    def _save_leaderboard(self, leaderboard: Leaderboard) -> None:
        self.db.leaderboard = [asdict(e) for e in leaderboard.entries()]

    @staticmethod
    def _publish_season_number(season_number: int) -> None:
        """Mirror the season number into ServerConfig for the death path (death.md §3)."""
        ServerConfig.objects.conf("current_season", value=season_number)

    # ── Tick: warnings then timed expiry ──────────────────────────────────────

    def at_repeat(self) -> None:
        state = self._season_state()
        now = time.time()

        due = state.due_warnings(now)
        for offset in due:
            self._broadcast(cfg.WANE_BROADCASTS.get(offset, "The season wanes."))
            state.mark_warned(offset)
        if due:
            self._save_season(state)

        if state.is_expired(now):
            self.end_season()

    # ── Reset entry points ────────────────────────────────────────────────────

    def end_season(self, reason: str | None = None) -> ResetReport:
        """Run the full reset immediately (spec §5) and open the next season.

        ``reason`` is the machine cause of an early end (e.g. ``"shrine_destroyed"``);
        when present a bespoke early-end broadcast precedes the new-season one.
        A timed expiry passes ``reason=None`` and skips the bespoke line.
        """
        now = time.time()
        if reason is not None:
            self._broadcast(cfg.EARLY_END_BROADCAST)

        state = self._season_state()
        leaderboard = self._leaderboard()
        survivors = self._gather_survivors()

        report = run_reset(state, leaderboard, self, survivors, now, reason)

        self._save_season(state)
        self._save_leaderboard(leaderboard)
        self._broadcast(cfg.NEW_SEASON_BROADCAST)
        logger.log_info(
            f"season_manager: season {report.closing_season} ended "
            f"(reason={reason or 'timer'}); season {report.new_season} begins."
        )
        return report

    def _gather_survivors(self) -> list[Survivor]:
        """Snapshot every living player character for the closing season (spec §4)."""
        survivors: list[Survivor] = []
        for char in Character.objects.all():
            level_trait = char.traits.level
            level = int(level_trait.value) if level_trait is not None else 1
            raw_class = char.db.char_class
            char_class = raw_class if isinstance(raw_class, str) and raw_class else "unknown"
            survivors.append(
                Survivor(
                    character_name=char.key,
                    char_class=char_class,
                    level=level,
                    hardcore=bool(char.hardcore),
                )
            )
        return survivors

    # ── Leaderboard API ───────────────────────────────────────────────────────

    def record_fell(self, character_name: str, char_class: str, level: int) -> LeaderboardEntry:
        """Append a hardcore death to the leaderboard immediately (spec §4; R7)."""
        leaderboard = self._leaderboard()
        entry = leaderboard.append_fell(
            character_name, char_class, level, self.db.season_number, time.time()
        )
        self._save_leaderboard(leaderboard)
        return entry

    def per_season(self, season_number: int | None = None) -> tuple[LeaderboardEntry, ...]:
        """Placements for a season (defaults to the current one; spec §4)."""
        season = season_number if season_number is not None else self.db.season_number
        return self._leaderboard().per_season(season)

    def all_time(self) -> tuple[LeaderboardEntry, ...]:
        """All-time placements ranked by level (spec §4)."""
        return self._leaderboard().all_time()

    # ── ResetHooks implementation (delegates to sibling managers) ──────────────

    def reset_factions(self) -> None:
        managers = search.search_script("faction_manager")
        if managers:
            managers[0].reset_season()

    def reset_repop(self) -> None:
        managers = search.search_script("repop_manager")
        if managers:
            managers[0].reset_season()

    def reset_priest(self) -> None:
        # The priest_manager lands at M12; until then this is a safe no-op so the
        # reset sequence stays whole.
        managers = search.search_script("priest_manager")
        if managers:
            managers[0].reset_season()

    def reset_shrine(self) -> None:
        managers = search.search_script("repop_manager")
        if managers:
            managers[0].reset_shrine()

    def revert_season_quests(self) -> None:
        # Season-global quest effects (e.g. a destroyed Shrine rebuilt) revert at
        # M13; logged no-op until the quest catalog exists.
        logger.log_info("season_manager: revert season-global quest effects (no-op pre-M13)")

    def rebuild_world(self) -> None:
        # Despawn stale live instances and re-populate the world from the zone
        # registries (world-build spec §10). The orchestrator owns *how* to
        # rebuild; this manager owns only reset *ordering* (R6 §3.3). Imported
        # lazily so the manager module stays free of the build package at load.
        from world.build import orchestrator  # noqa: PLC0415

        orchestrator.rebuild_world()

    def refresh_roster(self) -> None:
        # The henchmen tavern roster refreshes with the Keep zone (M7); logged
        # no-op until then.
        logger.log_info("season_manager: refresh henchmen roster (no-op pre-M7)")

    # ── Broadcast ─────────────────────────────────────────────────────────────

    @staticmethod
    def _broadcast(message: str) -> None:
        """Announce to every connected session (mirrors repop_manager._broadcast)."""
        if evennia.SESSION_HANDLER is not None:
            for session in evennia.SESSION_HANDLER.get_sessions():
                session.msg(message)

    # Satisfy mypy: Evennia base attributes accessed dynamically.
    db: Any
