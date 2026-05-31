"""FactionManager GlobalScript: persists FactionState in Evennia Attributes.

Pure faction logic lives in world.factions.state.FactionState; this script
is the long-lived Evennia owner that stores the state dicts across restarts
and drives the daily decay tick (each tick applies one `DECAY_PER_DAY`).

Usage (from anywhere in the running game)::

    from evennia.utils import search
    mgr = search.search_script("faction_manager")[0]
    mgr.apply_kill_member("kobold", str(player.id))
    band = mgr.standing_band("kobold", str(player.id))
"""

from __future__ import annotations

from typing import Any

from evennia.scripts.scripts import DefaultScript

from world.factions.state import FactionState


class FactionManager(DefaultScript):
    """Global script managing per-player faction standing and per-pair tension."""

    def at_script_creation(self) -> None:
        self.key = "faction_manager"
        self.desc = "Manages faction standings and tribe-pair tensions."
        # Decay is specified as DECAY_PER_DAY and at_repeat applies exactly one
        # decay_tick per fire, so the tick must be daily (86400s). An hourly
        # tick would decay 24x too fast (faction.md §2.3).
        self.interval = 86400
        self.persistent = True
        self.start_delay = True
        state = FactionState()
        self.db.standings = state.standings
        self.db.tensions = state.tensions

    # Load a fresh FactionState from persisted dicts; save back after mutations.
    def _faction_state(self) -> FactionState:
        return FactionState(
            standings=dict(self.db.standings or {}),
            tensions=dict(self.db.tensions or {}),
        )

    def _save(self, state: FactionState) -> None:
        self.db.standings = state.standings
        self.db.tensions = state.tensions

    def at_repeat(self) -> None:
        # Fires once per day (see interval); applies one DECAY_PER_DAY step.
        state = self._faction_state()
        state.decay_tick()
        self._save(state)

    # ── Standing API ────────────────────────────────────────────────────────

    def get_standing(self, faction_id: str, player_key: str) -> int:
        return self._faction_state().get_standing(faction_id, player_key)

    def standing_band(self, faction_id: str, player_key: str) -> str:
        return self._faction_state().standing_band(faction_id, player_key)

    def apply_kill_member(self, faction_id: str, player_key: str) -> None:
        state = self._faction_state()
        state.apply_kill_member(faction_id, player_key)
        self._save(state)

    def apply_kill_leader(self, faction_id: str, player_key: str) -> None:
        state = self._faction_state()
        state.apply_kill_leader(faction_id, player_key)
        self._save(state)

    def apply_quest_aid(self, faction_id: str, player_key: str) -> None:
        state = self._faction_state()
        state.apply_quest_aid(faction_id, player_key)
        self._save(state)

    def apply_quest_harm(self, faction_id: str, player_key: str) -> None:
        state = self._faction_state()
        state.apply_quest_harm(faction_id, player_key)
        self._save(state)

    def apply_bribe(self, faction_id: str, player_key: str) -> None:
        state = self._faction_state()
        state.apply_bribe(faction_id, player_key)
        self._save(state)

    # ── Relation API ────────────────────────────────────────────────────────

    def get_tension(self, faction_a: str, faction_b: str) -> int:
        return self._faction_state().get_tension(faction_a, faction_b)

    def relation_band(self, faction_a: str, faction_b: str) -> str:
        return self._faction_state().relation_band(faction_a, faction_b)

    def apply_quest_aid_vs(self, faction_a: str, faction_b: str) -> None:
        state = self._faction_state()
        state.apply_quest_aid_vs(faction_a, faction_b)
        self._save(state)

    def apply_leadership_broken(self, faction_id: str) -> None:
        state = self._faction_state()
        state.apply_leadership_broken(faction_id)
        self._save(state)

    # ── Lifecycle ───────────────────────────────────────────────────────────

    def reset_season(self) -> None:
        state = self._faction_state()
        state.reset_season()
        self._save(state)

    # Satisfy mypy: Evennia base attributes accessed dynamically.
    db: Any
