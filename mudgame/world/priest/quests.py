"""The spy's quest chain for the disguised-priest plot (R4 §4).

Pure Python — no Evennia imports — so the chain is unit-testable without booting
the server. While unexposed the spy offers benign-seeming quests flagged
``aids_cult`` in the quest catalog (R9/M13). Doing the spy's bidding is a trap:
completing ``SPY_QUESTS_TO_AMBUSH`` of them springs a scripted Caves ambush and
brands the player a cult collaborator, raising their standing with the cult (R2).

Like investigation evidence (``world.priest.evidence``), the quest log is
**per-character** (spec §1): one player's collaboration is their own. The engine
layer (the quest catalog's turn-in hook) records each completion here; when
``complete_spy_quest`` reports the ambush has sprung, the engine spawns the Caves
ambush and applies the cult standing gain via the faction_manager
(``apply_quest_aid`` on ``CULT_FACTION_ID``).
"""

from __future__ import annotations

from collections.abc import Iterable

from world.priest import config as _cfg


class SpyQuestLog:
    """One character's completed spy (``aids_cult``) quests (spec §4).

    ``completed`` holds the ids of distinct spy quests the character has turned
    in; it is a set, so re-turning the same quest never double-counts toward the
    ambush threshold.
    """

    def __init__(self, completed: Iterable[str] = ()) -> None:
        self.completed: set[str] = set(completed)

    @property
    def completed_count(self) -> int:
        """Number of distinct spy quests the character has completed."""
        return len(self.completed)

    @property
    def ambush_sprung(self) -> bool:
        """Whether the player has completed enough spy quests to spring the ambush."""
        return self.completed_count >= _cfg.SPY_QUESTS_TO_AMBUSH


def complete_spy_quest(log: SpyQuestLog, quest_id: str) -> bool:
    """Record completing an ``aids_cult`` spy quest; return whether it springs the ambush.

    Returns ``True`` only on the completion that *first* reaches
    ``SPY_QUESTS_TO_AMBUSH`` distinct quests — the single moment the Caves ambush
    fires and the player is branded a cult collaborator (cult standing rises).
    Re-turning an already-completed quest, and any completion before or after that
    threshold crossing, returns ``False`` so the ambush fires exactly once.
    """
    was_sprung = log.ambush_sprung
    newly = quest_id not in log.completed
    log.completed.add(quest_id)
    return newly and not was_sprung and log.ambush_sprung
