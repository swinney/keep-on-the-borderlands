"""PriestManager GlobalScript: owns the disguised priest's seasonal identity (R4).

Pure rotation logic lives in world.priest.state.PriestState; this script is the
long-lived Evennia owner that persists the current/previous spy across restarts
and re-rolls the identity at each season boundary.

The season_manager's ``reset_priest`` hook calls ``reset_season`` once per season
(R6 §3.3); the manager re-rolls the spy, never picking the NPC that just served,
and re-draws the spy's clue set (spec §2). Detection paths and the quest chain
are pure (world.priest.detection / .quests) and key off this manager's identity.

Exposure (spec §5) is owned here: ``report`` validates a reporting player's
per-character evidence against the global identity, flips the server-global
``exposed`` flag exactly once, broadcasts the unmasking, and flees the spy NPC to
the Shrine as a boss. The pure decision lives in world.priest.exposure.

Usage (from anywhere in the running game)::

    from evennia.utils import search
    mgr = search.search_script("priest_manager")[0]
    mgr.spy_id            # current season's disguised priest
    mgr.clue_ids          # the clues attached to this season's spy
    mgr.exposed           # whether the spy has been unmasked this season
    mgr.report(evidence)  # report to the Castellan with a player's evidence
"""

from __future__ import annotations

from random import Random
from typing import Any

import evennia
from evennia.scripts.scripts import DefaultScript
from evennia.utils import logger

from world.priest import config as _cfg
from world.priest import exposure
from world.priest.evidence import Evidence
from world.priest.state import PriestState


class PriestManager(DefaultScript):
    """Global script owning the rotating disguised-priest identity."""

    def at_script_creation(self) -> None:
        self.key = "priest_manager"
        self.desc = "Owns the disguised priest's rotating seasonal identity."
        self.persistent = True
        # Persisted plainly so Evennia Attributes can store them:
        #   spy_id   — the current season's spy NPC id (None before first roll)
        #   clue_ids — the clues attached to this season's spy (list of clue ids)
        #   exposed  — server-global flag: has the spy been unmasked this season
        self.db.spy_id = None
        self.db.clue_ids = []
        self.db.exposed = False
        # Seed the first season's identity and clue set immediately so the
        # chapel always has a fully-assigned spy from creation onward.
        self.assign_spy()
        self.assign_clues()

    # ── State (de)serialization ───────────────────────────────────────────────

    def _priest_state(self) -> PriestState:
        return PriestState(
            spy_id=self.db.spy_id,
            clue_ids=tuple(self.db.clue_ids or ()),
            exposed=bool(self.db.exposed),
        )

    def _save(self, state: PriestState) -> None:
        self.db.spy_id = state.spy_id
        self.db.clue_ids = list(state.clue_ids)
        self.db.exposed = state.exposed

    # ── Identity API ──────────────────────────────────────────────────────────

    @property
    def spy_id(self) -> str | None:
        """The current season's disguised-priest NPC id."""
        return self.db.spy_id

    @property
    def clue_ids(self) -> tuple[str, ...]:
        """The clues attached to this season's spy (spec §2 step 2)."""
        return tuple(self.db.clue_ids or ())

    @property
    def exposed(self) -> bool:
        """Whether the spy has been unmasked this season (spec §5)."""
        return bool(self.db.exposed)

    # ── Exposure (spec §5) ────────────────────────────────────────────────────

    def report(self, evidence: Evidence) -> bool:
        """Report the spy to the Castellan; return whether this report exposes him.

        Validates the reporting player's per-character ``evidence`` against the
        global identity (world.priest.exposure). On the single exposing report,
        flips the server-global ``exposed`` flag, broadcasts the unmasking, and
        flees the spy NPC to the Shrine as a cult boss (spec §5 steps 2-3),
        returning ``True``. Returns ``False`` for an insufficiently-evidenced
        report (rejected, spec §5 step 1) or one that arrives after the spy is
        already exposed (the secret is public; the world event never re-fires).
        """
        state = self._priest_state()
        spy_id = exposure.report_to_castellan(state, evidence)
        if spy_id is None:
            return False
        self._save(state)
        self._expose_spy(spy_id)
        return True

    def _expose_spy(self, spy_id: str) -> None:
        """Carry out the world reaction to an exposing report (spec §5 steps 2-3).

        Broadcasts the unmasking server-wide and flees the spy NPC from the
        chapel to the Shrine ``boss_lair``, where it is re-instantiated as a cult
        boss. Live mob relocation rides the same logged-stub path as
        repop_manager._instantiate until the spawner is wired; the canonical,
        observable effects — the global flag and the broadcast — fire here.
        """
        sdesc = _cfg.npc_by_id(spy_id).sdesc
        self._broadcast(_cfg.exposure_broadcast(sdesc))
        logger.log_info(
            f"priest_manager: spy {spy_id} unmasked; fleeing to Shrine "
            f"{_cfg.BOSS_LAIR_ROOM} as a cult boss."
        )

    @staticmethod
    def _broadcast(message: str) -> None:
        """Announce to every connected session (mirrors repop_manager._broadcast)."""
        if evennia.SESSION_HANDLER is not None:
            for session in evennia.SESSION_HANDLER.get_sessions():
                session.msg(message)

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

    def assign_clues(self, rng: Random | None = None) -> tuple[str, ...]:
        """Draw this season's clue set for the spy (spec §2 step 2).

        ``rng`` is injectable for deterministic tests; production passes a fresh
        ``Random`` so the draw is unpredictable.
        """
        state = self._priest_state()
        clue_ids = state.assign_clues(rng if rng is not None else Random())
        self._save(state)
        logger.log_info(f"priest_manager: spy clues are now {list(clue_ids)}.")
        return clue_ids

    # ── Season-reset hook (R6 §3.3; called by the season_manager) ─────────────

    def reset_season(self, rng: Random | None = None) -> None:
        """Re-roll the plot at the season boundary (spec §2, §6).

        The single reset transition: re-roll the spy (excluding the outgoing
        one) and re-draw its clue set, which also clears the server-global
        ``exposed`` flag (a fresh season's spy starts unmasked). The chapel is
        restored to its disguised 5-NPC staff and any Shrine boss instance from
        last season's exposure is removed (spec §6) — live mob teardown rides the
        same logged-stub path as ``_expose_spy`` until the spawner is wired.
        """
        state = self._priest_state()
        spy_id, clue_ids = state.reset_season(rng if rng is not None else Random())
        self._save(state)
        logger.log_info(
            f"priest_manager: season reset — spy is now {spy_id}, "
            f"clues {list(clue_ids)}; exposure cleared, chapel restored, "
            f"any Shrine {_cfg.BOSS_LAIR_ROOM} boss removed."
        )

    # Satisfy mypy: Evennia base attributes accessed dynamically.
    db: Any
