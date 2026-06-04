"""The four detection paths for the disguised-priest plot (R4 §3).

Pure Python — no Evennia imports — so each path is unit-testable without booting
the server. Every path keys off the global identity/clue assignment held by
``PriestState`` and records what it yields onto a per-character ``Evidence``
object (spec §1: investigation is private to each player).

The paths (spec §3):

* **Detect Evil** — a cleric of sufficient level reads the spy's evil aura: a
  strong proof. Innocents (and the spy under a too-low caster) show nothing.
* **Witnessing a night act** — at game-night the spy performs one of its
  ``night_act`` tells in a chapel room; a present player logs a clue sighting.
* **Planted object** — searching the spy's cell/the chapel turns up a
  ``planted_object`` tell: a clue sighting, or a strong proof if the object is
  itself a smoking gun (``Clue.is_proof``).
* **Curate dialogue** — once a player holds ``CURATE_CLUE_THRESHOLD`` sightings
  the Curate names a clue they have not yet seen, pointing them onward.

The engine layer (a ``cast detect evil`` target hook, the night-act ticker, a
``search`` extension, the Curate's dialogue) drives these; the rules live here.
"""

from __future__ import annotations

from world.priest import config as _cfg
from world.priest.evidence import Evidence
from world.priest.state import PriestState


def detect_evil(
    state: PriestState,
    target_npc_id: str,
    caster_level: int,
    evidence: Evidence,
) -> bool:
    """Detect Evil on ``target_npc_id``; return ``True`` if an evil aura shows.

    The spy radiates a detectable aura only to a caster of at least
    ``DETECT_EVIL_MIN_LEVEL`` (spec §3, "of sufficient level"). Innocent chapel
    NPCs — and the spy under a too-low caster — show nothing. A positive read
    records a strong proof on ``evidence``.
    """
    if caster_level < _cfg.DETECT_EVIL_MIN_LEVEL:
        return False
    if target_npc_id != state.spy_id:
        return False
    evidence.add_strong_proof(_cfg.PROOF_DETECT_EVIL)
    return True


def witness_night_act(
    state: PriestState,
    clue_id: str,
    evidence: Evidence,
    *,
    is_night: bool,
) -> bool:
    """Witness the spy's night-act tell; return ``True`` if a sighting is logged.

    The act only happens — and so can only be observed — at game-night, and only
    for a ``night_act`` clue actually attached to this season's spy. A successful
    observation logs a (newly seen) clue sighting on ``evidence``.
    """
    if not is_night:
        return False
    if clue_id not in state.clue_ids:
        return False
    if _cfg.clue_by_id(clue_id).tell != _cfg.TELL_NIGHT_ACT:
        return False
    return evidence.log_clue(clue_id)


def search_for_object(state: PriestState, evidence: Evidence) -> str | None:
    """Search the spy's cell/the chapel; return the planted clue id found, or None.

    Surfaces the spy's first ``planted_object`` tell. A smoking-gun object
    (``Clue.is_proof``) records a strong proof; an ordinary planted object logs a
    clue sighting. Returns ``None`` when the spy has no planted-object tell.
    """
    for clue_id in state.clue_ids:
        clue = _cfg.clue_by_id(clue_id)
        if clue.tell != _cfg.TELL_PLANTED_OBJECT:
            continue
        if clue.is_proof:
            evidence.add_strong_proof(clue_id)
        else:
            evidence.log_clue(clue_id)
        return clue_id
    return None


def curate_dialogue(state: PriestState, evidence: Evidence) -> str | None:
    """The Curate shares a clue once the player has enough sightings (spec §3).

    Stays silent below ``CURATE_CLUE_THRESHOLD`` logged sightings. Once unlocked,
    it names one of the spy's clues the player has not yet seen — a fresh
    sighting plus direction — or ``None`` if the player already knows them all.
    """
    if evidence.clue_count < _cfg.CURATE_CLUE_THRESHOLD:
        return None
    for clue_id in state.clue_ids:
        if clue_id not in evidence.clue_sightings:
            evidence.log_clue(clue_id)
            return clue_id
    return None
