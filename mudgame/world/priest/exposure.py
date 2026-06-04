"""Exposure flow for the disguised-priest plot (R4 §5).

Pure Python — no Evennia imports — so the report-and-expose transition is
unit-testable without booting the server. Investigation is per-character, but
**exposure is server-global and fires once** (spec §1): the first player to
report the spy to the Castellan with sufficient evidence trips a single world
reaction — the spy is unmasked and flees the chapel to become a Shrine boss
everyone can then confront.

This module owns the decision: it validates a reporter's ``Evidence`` against the
global ``PriestState`` and flips the global ``exposed`` flag. The engine layer
(``PriestManager.report``) wraps it to deliver the broadcast, relocate the spy
NPC to the Shrine, credit the reporter, and refill the chapel (spec §5 steps
2-5); the rule for *whether* exposure happens lives here.
"""

from __future__ import annotations

from world.priest.evidence import Evidence
from world.priest.state import PriestState


def report_to_castellan(state: PriestState, evidence: Evidence) -> str | None:
    """Report the spy to the Castellan; return the spy id to relocate, or None.

    Returns the unmasked spy's id **only on the single report that exposes him**
    — the caller uses it to relocate that NPC to the Shrine as a boss (spec §5
    step 3). Returns ``None`` when:

    * there is no spy assigned yet (``spy_id is None``) — there is nothing to
      expose, so the flag is left untouched; or
    * the reporter lacks sufficient evidence (one strong proof or three clue
      sightings) — the report is rejected, "suspicions, not proof" (spec §5
      step 1), and no exposure occurs; or
    * the spy is already exposed — the secret is public, so a later report is a
      no-op and never re-fires the world event.

    Exposure is server-global: the flag lives on the shared ``PriestState``, so a
    second reporter (even with their own valid evidence) finds it already set.
    """
    if state.exposed:
        return None
    if state.spy_id is None:
        return None
    if not evidence.can_report:
        return None
    state.exposed = True
    return state.spy_id
