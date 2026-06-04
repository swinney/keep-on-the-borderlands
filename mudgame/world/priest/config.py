"""Static configuration for the disguised-priest plot (R4).

Pure data — no Evennia imports — so the rotation core stays unit-testable. The
``PriestManager`` GlobalScript owns the live, persisted seasonal assignment.

This module is the single tuning location for the chapel cast (spec §2). The
clue pool, detection paths, and quest chain land with the later M12 slices and
extend this file rather than scatter their constants.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChapelNPC:
    """One member of the chapel staff; exactly one is the spy each season."""

    npc_id: str
    sdesc: str
    role: str


# The pool of chapel NPCs (spec §2). One is the disguised evil priest each
# season; identity rotates and never repeats back-to-back.
POOL: tuple[ChapelNPC, ...] = (
    ChapelNPC("anselm", "a soft-spoken friar", "almoner"),
    ChapelNPC("maeve", "a stern sister", "keeper of the reliquary"),
    ChapelNPC("ortho", "a portly deacon", "leads daily services"),
    ChapelNPC("bellan", "a young bellringer", "tends the chapel bell"),
    ChapelNPC("gisla", "a wandering pardoner", "sells indulgences"),
)

# Convenience view: the pool's NPC ids in declaration order.
POOL_IDS: tuple[str, ...] = tuple(npc.npc_id for npc in POOL)


def npc_by_id(npc_id: str) -> ChapelNPC:
    """Return the pool member with ``npc_id`` (raises ``KeyError`` if unknown)."""
    for npc in POOL:
        if npc.npc_id == npc_id:
            return npc
    raise KeyError(npc_id)
