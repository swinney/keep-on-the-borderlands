"""Per-character investigation evidence for the disguised-priest plot (R4 §3).

Pure Python — no Evennia imports — so the detection logic stays unit-testable.
Investigation is **per-character** (spec §1): every player gathers clues and
proof independently, and one player's progress never appears on another's. The
``PriestManager`` holds only the global identity/clue assignment and exposure
flag; this object is what a Character persists for its own hunt.

A player may report the spy once they hold either one *strong proof* (e.g. the
evil aura from Detect Evil, or a smoking-gun planted object) or
``CLUE_SIGHTINGS_TO_REPORT`` distinct *clue sightings* (spec §3).
"""

from __future__ import annotations

from collections.abc import Iterable

from world.priest import config as _cfg


class Evidence:
    """One character's gathered clue sightings and strong proofs (spec §3).

    ``clue_sightings`` holds the ids of distinct clues the character has
    observed; ``strong_proofs`` holds the sources of any conclusive proof
    (Detect Evil's aura or a smoking-gun object). Both are sets, so re-observing
    the same clue or re-confirming the same proof does not inflate the count.
    """

    def __init__(
        self,
        clue_sightings: Iterable[str] = (),
        strong_proofs: Iterable[str] = (),
    ) -> None:
        self.clue_sightings: set[str] = set(clue_sightings)
        self.strong_proofs: set[str] = set(strong_proofs)

    def log_clue(self, clue_id: str) -> bool:
        """Record a clue sighting; return ``True`` only if it was newly seen."""
        if clue_id in self.clue_sightings:
            return False
        self.clue_sightings.add(clue_id)
        return True

    def add_strong_proof(self, source: str) -> bool:
        """Record a strong proof by source; return ``True`` if newly confirmed."""
        if source in self.strong_proofs:
            return False
        self.strong_proofs.add(source)
        return True

    @property
    def clue_count(self) -> int:
        """Number of distinct clues the character has sighted."""
        return len(self.clue_sightings)

    @property
    def can_report(self) -> bool:
        """Whether the character has enough evidence to report (spec §3).

        Satisfied by one strong proof or ``CLUE_SIGHTINGS_TO_REPORT`` distinct
        clue sightings.
        """
        return bool(self.strong_proofs) or (self.clue_count >= _cfg.CLUE_SIGHTINGS_TO_REPORT)
