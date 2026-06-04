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


# ── Clue pool (spec §2) ──────────────────────────────────────────────────────
#
# Each season the spy is assigned ``CLUE_COUNT`` distinct clues from this pool.
# A clue is not just lore text: each carries a ``tell`` category naming the
# observable hook the detection paths (§3) key off. The detection slice consumes
# those categories; this slice only draws and attaches the set.

# The detection-path category a clue's tell belongs to. The M12 detection slice
# routes each path off these:
#   night_act       — the spy performs the tell at game-night in a chapel room
#   planted_object  — a clue object found by searching the spy's cell/the chapel
#   dialogue        — a verbal slip surfaced via the Curate / prayer observation
#   observed        — a passive tell anyone present can notice
TELL_NIGHT_ACT = "night_act"
TELL_PLANTED_OBJECT = "planted_object"
TELL_DIALOGUE = "dialogue"
TELL_OBSERVED = "observed"


@dataclass(frozen=True)
class Clue:
    """One clue the spy may exhibit, with the tell the detection paths observe.

    ``is_proof`` marks a planted object that is itself a smoking gun — finding it
    yields a *strong proof*, not merely a clue sighting (spec §3, planted-object
    row: "strong if the object is itself proof").
    """

    clue_id: str
    text: str
    tell: str
    is_proof: bool = False


# The seven canonical clues (spec §2). One season's spy gets a random
# ``CLUE_COUNT``-sized subset.
CLUE_POOL: tuple[Clue, ...] = (
    Clue("black_candles", "lights black candles at midnight", TELL_NIGHT_ACT),
    Clue("black_dagger", "owns a black-handled dagger", TELL_PLANTED_OBJECT),
    Clue(
        "shrine_password",
        "knows the Shrine's password",
        TELL_PLANTED_OBJECT,
        is_proof=True,
    ),
    Clue("holy_water", "flinches from holy water", TELL_OBSERVED),
    Clue("omits_litany", "omits the Lawful litany at prayer", TELL_DIALOGUE),
    Clue("hooded_visitor", "meets a hooded visitor after dark", TELL_NIGHT_ACT),
    Clue("wary_cat", "the chapel cat will not approach", TELL_OBSERVED),
)

# Convenience view: the clue ids in declaration order.
CLUE_IDS: tuple[str, ...] = tuple(clue.clue_id for clue in CLUE_POOL)

# How many distinct clues attach to the spy each season (spec §2 step 2).
CLUE_COUNT = 3


def clue_by_id(clue_id: str) -> Clue:
    """Return the clue with ``clue_id`` (raises ``KeyError`` if unknown)."""
    for clue in CLUE_POOL:
        if clue.clue_id == clue_id:
            return clue
    raise KeyError(clue_id)


# ── Detection thresholds (spec §3) ───────────────────────────────────────────
#
# A player may report once they hold one strong proof OR this many distinct clue
# sightings; the Curate only opens up once they have logged a smaller number.

# Distinct clue sightings that, on their own, license a report (spec §3:
# "one strong proof or three clue sightings").
CLUE_SIGHTINGS_TO_REPORT = 3

# Clue sightings the player must already hold before the Curate will share
# suspicions (spec §3, Curate row: "once the player has logged ≥2 clue
# sightings").
CURATE_CLUE_THRESHOLD = 2

# Minimum cleric level for Detect Evil to read the spy's aura. CLAUDE.md §2 and
# spec §3 both gate this on a *high-level* caster (Detect Evil is otherwise a
# 1st-level cleric spell); 5 is the midpoint of the 1-10 B2-scaled band. Tuning
# knob — adjust here, not in the detection logic.
DETECT_EVIL_MIN_LEVEL = 5

# Source label recorded for a strong proof obtained via Detect Evil.
PROOF_DETECT_EVIL = "detect_evil"
