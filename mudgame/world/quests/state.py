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

Prereq gating (quests.md §1, §6, §9.2/§9.5) is enforced by ``prereqs_met``: a
quest opens only when the character's level, completed prior quests, faction
standing, and (for the priest-plot quests) evidence all clear the gate. Standing
is compared against the faction ladder (``world.factions.config``); a tribe with
no recorded standing defaults to neutral, matching ``FactionState.standing_band``,
so tribe-chief quests are offered to a fresh character but withdrawn once they go
hostile to the giver tribe.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import NotRequired, TypedDict

from world.factions.config import STANDING_LADDER, band_for
from world.quests.config import BOUNTY_COOLDOWN_SECONDS, KillStep, Quest, StandingGate

# Displayed quest states (quests.md §1).
NOT_OFFERED = "not_offered"
AVAILABLE = "available"
ACTIVE = "active"
COMPLETE = "complete"

# Standing band → ladder rank (0 = worst, higher = better), built from the single
# faction ladder so the quest gate and the faction system never disagree on order.
_STANDING_RANK: dict[str, int] = {label: rank for rank, (label, _) in enumerate(STANDING_LADDER)}

# A (faction, player) pair with no recorded standing sits at reputation 0, which
# the ladder reads as this band — the same default as ``FactionState.standing_band``.
DEFAULT_STANDING_BAND: str = band_for(0, STANDING_LADDER)


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
    # Set True by the world event that satisfies a deed objective (``record_deed``).
    # Absent on entries minted before deeds were tracked, so always read via
    # ``deed_satisfied``/``.get``.
    deed_done: NotRequired[bool]


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


def is_deed_only(quest: Quest) -> bool:
    """True when ``quest`` has no kill steps — a pure world-event deed (quests.md §1).

    The kill-tracker has nothing to count for such a quest, so ``steps_met`` is
    vacuously true; its real completion rides a deed-completion flag set by the
    world event that satisfies the deed (``record_deed``).
    """
    return not kill_steps(quest)


def requires_deed_flag(quest: Quest) -> bool:
    """True when turn-in must wait for a world-event deed-completion flag.

    Closes the deed-quest turn-in exploit (tasks.md M13): a deed-only quest cannot
    be accepted and instantly turned in for its reward — ``commands.quests`` refuses
    the turn-in until a world event has set the entry's ``deed_done`` flag
    (``record_deed``). The one exception is a quest whose deed *is* the turn-in
    interaction — an evidence-gated report such as ``c_expose_priest`` (report the
    spy) or ``cu_suspicions`` (hear the Curate's doubts) — which stays gated by its
    evidence requirement, not a prior flag (quests.md §3-§4).
    """
    return is_deed_only(quest) and quest.evidence_min is None


def deed_satisfied(entry: QuestEntry) -> bool:
    """True when a world event has marked this entry's deed done."""
    return bool(entry.get("deed_done", False))


def remaining(quest: Quest, progress: Mapping[str, int]) -> dict[str, int]:
    """Kills still owed per faction (never negative)."""
    return {
        step.faction: max(0, step.count - progress.get(step.faction, 0))
        for step in kill_steps(quest)
    }


def standing_ok(gate: StandingGate, standings: Mapping[str, str]) -> bool:
    """True when the character's band for ``gate.faction`` is at least ``min_band``.

    Bands are ranked against the faction ladder (worst→best); a faction absent
    from ``standings`` defaults to ``DEFAULT_STANDING_BAND`` (neutral), so a fresh
    character clears a "non-hostile" tribe-chief gate but a player who has turned
    the tribe hostile does not (quests.md §6, §9.5).
    """
    have = standings.get(gate.faction, DEFAULT_STANDING_BAND)
    return _STANDING_RANK.get(have, 0) >= _STANDING_RANK[gate.min_band]


def prereqs_met(
    quest: Quest,
    *,
    level: int,
    log: Mapping[str, QuestEntry] | None = None,
    standings: Mapping[str, str] | None = None,
    has_evidence: bool = False,
) -> bool:
    """True when every prerequisite for ``quest`` is satisfied (quests.md §1, §9.2).

    Gates, all of which must clear: the character's ``level`` meets ``min_level``;
    each ``prereq_quests`` id is stored ``complete`` in ``log``; each
    ``standing_gates`` faction is at non-hostile (or better) standing; and, for a
    quest carrying an ``evidence_min`` grade, ``has_evidence`` is true. The caller
    evaluates that grade against the player's evidence and passes the result here,
    so this pure layer stays priest-agnostic. ``log``/``standings`` default to
    empty, so an unsupplied prerequisite reads as unmet.
    """
    if level < quest.min_level:
        return False
    completed = log or {}
    for prior_id in quest.prereq_quests:
        prior = completed.get(prior_id)
        if prior is None or prior["state"] != COMPLETE:
            return False
    standing_map = standings or {}
    if not all(standing_ok(gate, standing_map) for gate in quest.standing_gates):
        return False
    return not (quest.evidence_min is not None and not has_evidence)


def status(
    quest: Quest,
    entry: QuestEntry | None,
    *,
    level: int,
    now: float,
    log: Mapping[str, QuestEntry] | None = None,
    standings: Mapping[str, str] | None = None,
    has_evidence: bool = False,
) -> str:
    """Derive the displayed state for ``quest`` from its stored ``entry``.

    With no entry the quest is ``available`` once all prereqs clear (level, prior
    quests, faction standing, evidence — ``prereqs_met``), else ``not_offered``. A
    repeatable bounty stored as ``complete`` becomes ``available`` again once its
    cooldown elapses *and* its prereqs still hold (quests.md §1, §9.2, §9.10).
    """
    open_for_accept = prereqs_met(
        quest, level=level, log=log, standings=standings, has_evidence=has_evidence
    )
    if entry is None:
        return AVAILABLE if open_for_accept else NOT_OFFERED
    stored = entry["state"]
    if stored == COMPLETE and quest.repeatable and now >= entry["cooldown_until"]:
        return AVAILABLE if open_for_accept else NOT_OFFERED
    return stored


def can_accept(
    quest: Quest,
    entry: QuestEntry | None,
    *,
    level: int,
    now: float,
    log: Mapping[str, QuestEntry] | None = None,
    standings: Mapping[str, str] | None = None,
    has_evidence: bool = False,
) -> bool:
    """True when ``quest`` is in the ``available`` state for this character."""
    return (
        status(
            quest,
            entry,
            level=level,
            now=now,
            log=log,
            standings=standings,
            has_evidence=has_evidence,
        )
        == AVAILABLE
    )


def accept(quest: Quest, entry: QuestEntry | None) -> QuestEntry:
    """Return a fresh ``active`` entry, preserving prior completion history."""
    prior = entry["times_completed"] if entry is not None else 0
    return {
        "state": ACTIVE,
        "progress": fresh_progress(quest),
        "times_completed": prior,
        "cooldown_until": 0.0,
        "deed_done": False,
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
        "deed_done": deed_satisfied(entry),
    }


def record_deed(log: QuestLog, quest_id: str) -> bool:
    """Mark the active ``quest_id`` entry's deed done (mutates ``log``); return change.

    The seam a world event calls when it satisfies a deed objective — the Altar
    shattering (the shrine-destroyed marker), rations delivered, a captive escorted
    home, a spy package dropped. Returns True only when it actually flips an active
    entry's flag, so the caller can skip the write-back when nothing changed (mirrors
    ``record_faction_kill``). No-op for a missing, non-active, or already-flagged
    entry.
    """
    entry = log.get(quest_id)
    if entry is None or entry["state"] != ACTIVE or deed_satisfied(entry):
        return False
    entry["deed_done"] = True
    return True


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
