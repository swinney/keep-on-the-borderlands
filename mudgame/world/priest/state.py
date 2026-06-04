"""Pure-Python disguised-priest state: seasonal identity rotation (R4 §2).

No Evennia imports — fully unit-testable without booting the server. The
``PriestManager`` GlobalScript (world/managers/priest_manager.py) wraps this
class and persists the assignment via Evennia Attributes.

This slice owns the rotating identity and the seasonal clue set: at each season
start the spy is re-rolled — chosen at random but never equal to the immediately
preceding season's spy (spec §2 step 1, §7 behaviors 1-2) — and a fresh set of
``CLUE_COUNT`` distinct clues is drawn from the clue pool and attached to it
(spec §2 step 2, §7 behavior 3). Detection, the quest chain, and exposure extend
this state in the later M12 slices.
"""

from __future__ import annotations

from random import Random

from world.priest import config as _cfg


class PriestState:
    """Holds the rotating spy identity and seasonal clue set across seasons.

    ``spy_id`` is the current season's spy (``None`` before the first
    assignment). ``assign_spy`` re-rolls it, excluding the outgoing spy so the
    same NPC never serves two seasons running. ``clue_ids`` is the set of clues
    attached to that spy; ``assign_clues`` re-draws it each season.
    """

    def __init__(
        self,
        spy_id: str | None = None,
        clue_ids: tuple[str, ...] = (),
    ) -> None:
        self.spy_id: str | None = spy_id
        self.clue_ids: tuple[str, ...] = tuple(clue_ids)

    def assign_spy(self, rng: Random) -> str:
        """Roll a new spy for the season and return its id (spec §2 step 1).

        The pick is drawn from the pool excluding the current ``spy_id`` (the
        immediately preceding season's spy), guaranteeing no back-to-back
        repeat. On the first assignment, with no prior spy, the whole pool is
        eligible.
        """
        candidates = [npc_id for npc_id in _cfg.POOL_IDS if npc_id != self.spy_id]
        self.spy_id = rng.choice(candidates)
        return self.spy_id

    def assign_clues(self, rng: Random) -> tuple[str, ...]:
        """Draw a fresh ``CLUE_COUNT``-clue set for the spy (spec §2 step 2).

        The draw is ``CLUE_COUNT`` distinct clues sampled from the full clue
        pool, replacing any previous season's set. Returns the new ``clue_ids``.
        """
        self.clue_ids = tuple(rng.sample(_cfg.CLUE_IDS, _cfg.CLUE_COUNT))
        return self.clue_ids
