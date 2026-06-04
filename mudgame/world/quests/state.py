"""Per-character quest state machine (docs/specs/quests.md §1, §9).

Pure and Evennia-free: every function operates on plain, JSON-serialisable dicts
so the accounting is unit-tested without booting the server and persists straight
onto ``character.db.quests`` (a ``QuestLog``). The Evennia layer
(``commands.quests``, ``typeclasses.npcs``) reads the log, calls these helpers,
and writes the result back.

State model (quests.md §1): ``not_offered → available → active → complete``. Only
``active``/``complete`` are *stored* per character; ``available``/``not_offered``
are derived from prereqs (and, for a repeatable bounty past its cooldown, from a
stored ``complete``). ``status`` performs that derivation.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TypedDict

from world.quests.config import BOUNTY_COOLDOWN_SECONDS, KillStep, Quest

# Displayed quest states (quests.md §1).
NOT_OFFERED = "not_offered"
AVAILABLE = "available"
ACTIVE = "active"
COMPLETE = "complete"


def kill_steps(quest: Quest) -> tuple[KillStep, ...]:
    """The quest's kill-count objectives only (quests.md §1).

    The pure state machine tracks kill progress; non-kill ``DeedStep`` objectives
    (fetch / escort / report / deliver / donate / bribe) are resolved by engine
    events, so this filters them out. A quest with no kill steps has nothing for
    the tracker to count — ``steps_met`` is then vacuously true and its completion
    is driven entirely by the engine deed.
    """
    return tuple(step for step in quest.steps if isinstance(step, KillStep))


class QuestEntry(TypedDict):
    """The per-character record stored under ``character.db.quests[quest_id]``."""

    state: str
    progress: dict[str, int]  # faction -> kills credited so far
    times_completed: int
    cooldown_until: float  # epoch seconds; 0.0 when not on cooldown


QuestLog = dict[str, QuestEntry]


def fresh_progress(quest: Quest) -> dict[str, int]:
    """A zeroed progress map covering every kill-step faction in ``quest``."""
    return {step.faction: 0 for step in kill_steps(quest)}


def steps_met(quest: Quest, progress: Mapping[str, int]) -> bool:
    """True when every kill step has reached its required count.

    A quest with no kill steps (a pure deed) is vacuously met by this tracker; its
    real completion is gated by the engine event that satisfies the deed.
    """
    return all(progress.get(step.faction, 0) >= step.count for step in kill_steps(quest))


def remaining(quest: Quest, progress: Mapping[str, int]) -> dict[str, int]:
    """Kills still owed per faction (never negative)."""
    return {
        step.faction: max(0, step.count - progress.get(step.faction, 0))
        for step in kill_steps(quest)
    }


def status(quest: Quest, entry: QuestEntry | None, *, level: int, now: float) -> str:
    """Derive the displayed state for ``quest`` from its stored ``entry``.

    With no entry the quest is ``available`` once the level prereq is met, else
    ``not_offered``. A repeatable bounty stored as ``complete`` becomes
    ``available`` again once its cooldown elapses (quests.md §1, §9.10).
    """
    if entry is None:
        return AVAILABLE if level >= quest.min_level else NOT_OFFERED
    stored = entry["state"]
    if stored == COMPLETE and quest.repeatable and now >= entry["cooldown_until"]:
        return AVAILABLE if level >= quest.min_level else NOT_OFFERED
    return stored


def can_accept(quest: Quest, entry: QuestEntry | None, *, level: int, now: float) -> bool:
    """True when ``quest`` is in the ``available`` state for this character."""
    return status(quest, entry, level=level, now=now) == AVAILABLE


def accept(quest: Quest, entry: QuestEntry | None) -> QuestEntry:
    """Return a fresh ``active`` entry, preserving prior completion history."""
    prior = entry["times_completed"] if entry is not None else 0
    return {
        "state": ACTIVE,
        "progress": fresh_progress(quest),
        "times_completed": prior,
        "cooldown_until": 0.0,
    }


def credit_kill(quest: Quest, progress: Mapping[str, int], faction: str) -> dict[str, int]:
    """Return progress with one kill of ``faction`` credited (capped at the step count)."""
    updated = dict(progress)
    for step in kill_steps(quest):
        if step.faction == faction:
            updated[faction] = min(step.count, updated.get(faction, 0) + 1)
    return updated


def turn_in(quest: Quest, entry: QuestEntry, *, now: float) -> QuestEntry:
    """Record a completed turn-in: ``complete``, history bumped, cooldown armed.

    A repeatable bounty arms a cooldown after which ``status`` reports it
    ``available`` again; a one-shot story quest stays ``complete``.
    """
    cooldown = now + BOUNTY_COOLDOWN_SECONDS if quest.repeatable else 0.0
    return {
        "state": COMPLETE,
        "progress": dict(entry["progress"]),
        "times_completed": entry["times_completed"] + 1,
        "cooldown_until": cooldown,
    }


def record_faction_kill(log: QuestLog, catalog: Mapping[str, Quest], faction: str) -> bool:
    """Credit one ``faction`` kill to every ``active`` quest tracking it (mutates ``log``).

    Returns True when any quest's progress advanced, so the caller can skip the
    write-back to ``character.db.quests`` when nothing changed.
    """
    changed = False
    for quest_id, entry in log.items():
        if entry["state"] != ACTIVE:
            continue
        quest = catalog.get(quest_id)
        if quest is None:
            continue
        before = entry["progress"]
        after = credit_kill(quest, before, faction)
        if after != before:
            entry["progress"] = after
            changed = True
    return changed
