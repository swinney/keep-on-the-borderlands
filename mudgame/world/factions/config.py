"""Faction configuration — all tunable thresholds live here.

Pure data: no Evennia imports, fully unit-testable without booting the server.
See docs/specs/faction.md for design rationale and the §3 tribe-pair matrix.
"""

from __future__ import annotations

from typing import TypedDict

# ---------------------------------------------------------------------------
# Standing bands: per (faction, player) hidden-integer reputation R
# ---------------------------------------------------------------------------
# Each entry is (label, lower_bound_inclusive).  The first entry has no lower
# bound (None) — it catches every score below the next band's threshold.
# Sorted lowest-band first (most negative rep) to highest.
STANDING_LADDER: list[tuple[str, int | None]] = [
    ("kill-on-sight", None),  # R <= -30
    ("hostile", -29),  # -29 .. -15
    ("neutral", -14),  # -14 .. +14
    ("friendly", +15),  # R >= +15
]

# ---------------------------------------------------------------------------
# Relation bands: per unordered {faction_a, faction_b} hidden-integer tension T
# ---------------------------------------------------------------------------
RELATION_LADDER: list[tuple[str, int | None]] = [
    ("allied", None),  # T <= -10
    ("peaceful", -9),  # -9 .. +4
    ("tense", +5),  # +5 .. +19
    ("war", +20),  # T >= +20
]


def band_for(score: int, ladder: list[tuple[str, int | None]]) -> str:
    """Return the band label for *score* against *ladder* (sorted low→high).

    Iterates the ladder and returns the label of the highest band whose
    lower bound is <= score.  The first entry (None bound) is the floor.
    """
    result = ladder[0][0]
    for label, lower in ladder:
        if lower is not None and score >= lower:
            result = label
    return result


# ---------------------------------------------------------------------------
# Event deltas — standing (per-player) and relation (per-pair)
# ---------------------------------------------------------------------------
STANDING_EVENTS: dict[str, int] = {
    "kill_member": -3,
    "kill_leader": -8,
    "quest_aid": +10,
    "quest_harm": -10,
    "bribe": +5,  # capped at neutral ceiling; enforced in FactionState.apply_bribe
}
RELATION_EVENTS: dict[str, int] = {
    "kill_member_thaw": -1,  # per rival currently tense/war
    "quest_aid_vs": +8,  # escalates a pair toward war
    "leadership_broken": +6,  # per rival when chief+shaman die
}

# Breaking an alliance (bribing the ogre to abandon the goblins, quests.md §8.6)
# dissolves the bond without making enemies: the pair leaves the "allied" band
# and cools to the bottom of "peaceful" (one above allied's ceiling of -10).
BROKEN_ALLIANCE_TENSION: int = -9

# ---------------------------------------------------------------------------
# Decay (anti-griefing: drift toward season-initial, never past it)
# ---------------------------------------------------------------------------
DECAY_ENABLED: bool = True
DECAY_PER_DAY: int = 1

# ---------------------------------------------------------------------------
# Initial tribe-pair tension matrix (§3) — mirrors B2 module politics
# ---------------------------------------------------------------------------
# Keys are frozenset({faction_a_id, faction_b_id}); values are initial T.
# Pairs not listed here default to DEFAULT_RELATION.
# minotaur and owlbear are omitted (solitary, no pair politics).
INITIAL_RELATIONS: dict[frozenset[str], int] = {
    # kobold
    frozenset({"kobold", "orc_vol"}): +12,
    frozenset({"kobold", "orc_dec"}): +12,
    frozenset({"kobold", "goblin"}): +10,
    frozenset({"kobold", "hobgoblin"}): +8,
    frozenset({"kobold", "gnoll"}): +14,
    frozenset({"kobold", "bugbear"}): +14,
    frozenset({"kobold", "ogre"}): +2,
    frozenset({"kobold", "cult"}): +6,
    # orc_vol
    frozenset({"orc_vol", "orc_dec"}): +24,  # blood enemies (war)
    frozenset({"orc_vol", "goblin"}): +10,
    frozenset({"orc_vol", "hobgoblin"}): +8,
    frozenset({"orc_vol", "gnoll"}): +12,
    frozenset({"orc_vol", "bugbear"}): +10,
    frozenset({"orc_vol", "ogre"}): +2,
    frozenset({"orc_vol", "cult"}): +6,
    # orc_dec
    frozenset({"orc_dec", "goblin"}): +10,
    frozenset({"orc_dec", "hobgoblin"}): +8,
    frozenset({"orc_dec", "gnoll"}): +12,
    frozenset({"orc_dec", "bugbear"}): +10,
    frozenset({"orc_dec", "ogre"}): +2,
    frozenset({"orc_dec", "cult"}): +6,
    # goblin
    frozenset({"goblin", "hobgoblin"}): +12,
    frozenset({"goblin", "gnoll"}): +20,  # gnolls raid the goblin warren (war)
    frozenset({"goblin", "bugbear"}): +14,
    frozenset({"goblin", "ogre"}): -10,  # ogre fights for goblins (allied)
    frozenset({"goblin", "cult"}): +6,
    # hobgoblin
    frozenset({"hobgoblin", "gnoll"}): +10,
    frozenset({"hobgoblin", "bugbear"}): +6,
    frozenset({"hobgoblin", "ogre"}): +2,
    frozenset({"hobgoblin", "cult"}): +4,  # cult's first convert (peaceful)
    # gnoll
    frozenset({"gnoll", "bugbear"}): +10,
    frozenset({"gnoll", "ogre"}): +2,
    frozenset({"gnoll", "cult"}): +6,
    # bugbear
    frozenset({"bugbear", "ogre"}): +2,
    frozenset({"bugbear", "cult"}): +6,
    # ogre
    frozenset({"ogre", "cult"}): +2,
    # keep ↔ cult: archenemies; keep holds no other tribe-pair entries
    frozenset({"keep", "cult"}): +24,
}

# Any faction pair not in INITIAL_RELATIONS starts at this tension (tense).
DEFAULT_RELATION: int = +12

# ---------------------------------------------------------------------------
# Faction definitions — static properties, used by manager and typeclasses
# ---------------------------------------------------------------------------


class FactionDef(TypedDict):
    display: str
    kind: str  # tribe | mercenary | beast | solitary | lawful | cult
    can_parley: bool


FACTIONS: dict[str, FactionDef] = {
    "kobold": {"display": "the kobolds", "kind": "tribe", "can_parley": True},
    "orc_vol": {"display": "the orcs of the Vile Rune", "kind": "tribe", "can_parley": True},
    "orc_dec": {"display": "the orcs of the Decapitator", "kind": "tribe", "can_parley": True},
    "goblin": {"display": "the goblins", "kind": "tribe", "can_parley": True},
    "hobgoblin": {"display": "the hobgoblins", "kind": "tribe", "can_parley": True},
    "gnoll": {"display": "the gnolls", "kind": "tribe", "can_parley": True},
    "bugbear": {"display": "the bugbears", "kind": "tribe", "can_parley": True},
    "ogre": {"display": "the ogre", "kind": "mercenary", "can_parley": True},
    "minotaur": {"display": "the minotaur", "kind": "solitary", "can_parley": False},
    "owlbear": {"display": "the owlbear", "kind": "beast", "can_parley": False},
    "cult": {"display": "the Cult of Evil Chaos", "kind": "cult", "can_parley": False},
    "keep": {"display": "the Keep garrison", "kind": "lawful", "can_parley": True},
    # M8 wilderness factions (minor, no Caves leadership/repop politics)
    "beast": {"display": "wild beasts", "kind": "beast", "can_parley": False},
    "bandit": {"display": "bandits", "kind": "mercenary", "can_parley": True},
    "lizard": {"display": "the lizard folk", "kind": "tribe", "can_parley": True},
}
