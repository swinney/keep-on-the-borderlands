"""Tests for the faction system (R2).

Derived from openspec/changes/b2-mud-v1-design/specs/faction-system/spec.md and
docs/specs/faction.md §7.

Config-level tests (band_for, initial matrix) are active.
FactionState tests (event processing, decay, season reset) are active as of
the faction_manager task.  NPC-aggression tests remain skipped until that task.
"""

import pytest

import world.factions.config as faction_cfg
from world.factions.config import (
    DEFAULT_RELATION,
    INITIAL_RELATIONS,
    RELATION_LADDER,
    STANDING_LADDER,
    band_for,
)
from world.factions.state import FactionState


def test_band_for_maps_standing_boundaries() -> None:
    """WHEN reputation is +15/+14/-15/-30 THEN bands are friendly/neutral/hostile/KOS."""
    assert band_for(+15, STANDING_LADDER) == "friendly"
    assert band_for(+14, STANDING_LADDER) == "neutral"
    assert band_for(-14, STANDING_LADDER) == "neutral"
    assert band_for(-15, STANDING_LADDER) == "hostile"
    assert band_for(-29, STANDING_LADDER) == "hostile"
    assert band_for(-30, STANDING_LADDER) == "kill-on-sight"
    assert band_for(0, STANDING_LADDER) == "neutral"
    assert band_for(+100, STANDING_LADDER) == "friendly"
    assert band_for(-100, STANDING_LADDER) == "kill-on-sight"


def test_band_for_maps_relation_boundaries() -> None:
    """WHEN tension is -10/-9/+5/+20 THEN bands are allied/peaceful/tense/war."""
    assert band_for(-10, RELATION_LADDER) == "allied"
    assert band_for(-9, RELATION_LADDER) == "peaceful"
    assert band_for(+4, RELATION_LADDER) == "peaceful"
    assert band_for(+5, RELATION_LADDER) == "tense"
    assert band_for(+19, RELATION_LADDER) == "tense"
    assert band_for(+20, RELATION_LADDER) == "war"
    assert band_for(-100, RELATION_LADDER) == "allied"
    assert band_for(+100, RELATION_LADDER) == "war"


def test_five_kills_make_standing_hostile() -> None:
    """WHEN a player kills five faction members THEN standing is hostile (R=-15)."""
    state = FactionState()
    for _ in range(5):
        state.apply_kill_member("kobold", "p1")
    assert state.get_standing("kobold", "p1") == -15
    assert state.standing_band("kobold", "p1") == "hostile"


def test_ten_kills_make_standing_kill_on_sight() -> None:
    """WHEN a player kills ten faction members THEN standing is kill-on-sight (R=-30)."""
    state = FactionState()
    for _ in range(10):
        state.apply_kill_member("kobold", "p1")
    assert state.get_standing("kobold", "p1") == -30
    assert state.standing_band("kobold", "p1") == "kill-on-sight"


def test_killing_leader_costs_eight() -> None:
    """WHEN a player kills a chief or shaman THEN reputation drops by 8."""
    state = FactionState()
    state.apply_kill_leader("kobold", "p1")
    assert state.get_standing("kobold", "p1") == -8
    assert state.standing_band("kobold", "p1") == "neutral"
    state.apply_kill_leader("kobold", "p1")
    assert state.get_standing("kobold", "p1") == -16
    assert state.standing_band("kobold", "p1") == "hostile"


def test_quest_aid_and_harm_move_standing_by_ten() -> None:
    """WHEN a player completes an aiding/harming quest THEN standing moves +/-10."""
    state = FactionState()
    state.apply_quest_aid("kobold", "p1")
    assert state.get_standing("kobold", "p1") == 10
    state.apply_quest_harm("kobold", "p1")
    assert state.get_standing("kobold", "p1") == 0
    state.apply_quest_harm("kobold", "p1")
    assert state.get_standing("kobold", "p1") == -10
    assert state.standing_band("kobold", "p1") == "neutral"


def test_bribe_cannot_exceed_neutral() -> None:
    """WHEN a player bribes past +15 THEN standing rises no higher than neutral."""
    state = FactionState()
    # Bribe from a high-neutral starting point: 12 + 5 would be 17, capped to 14.
    state.standings[("kobold", "p1")] = 12
    state.apply_bribe("kobold", "p1")
    assert state.get_standing("kobold", "p1") == 14
    assert state.standing_band("kobold", "p1") == "neutral"
    # Bribe again from the cap: stays at 14.
    state.apply_bribe("kobold", "p1")
    assert state.get_standing("kobold", "p1") == 14
    # Bribe from hostile: normal +5, no cap triggered.
    state2 = FactionState()
    state2.standings[("kobold", "p2")] = -20
    state2.apply_bribe("kobold", "p2")
    assert state2.get_standing("kobold", "p2") == -15


def test_killing_members_thaws_only_tense_or_war_rivals() -> None:
    """WHEN a player kills faction members THEN tension drops only with tense/war rivals."""
    state = FactionState()
    # kobold-goblin: tense (+10); kobold-ogre: peaceful (+2).
    initial_goblin = state.get_tension("kobold", "goblin")
    initial_ogre = state.get_tension("kobold", "ogre")
    assert band_for(initial_goblin, RELATION_LADDER) == "tense"
    assert band_for(initial_ogre, RELATION_LADDER) == "peaceful"

    state.apply_kill_member("kobold", "p1")

    assert state.get_tension("kobold", "goblin") == initial_goblin - 1
    assert state.get_tension("kobold", "ogre") == initial_ogre


def test_kobold_goblin_crosses_tense_to_peaceful() -> None:
    """WHEN enough kobolds die THEN kobold-goblin relation becomes peaceful."""
    state = FactionState()
    assert state.relation_band("kobold", "goblin") == "tense"
    for _ in range(6):
        state.apply_kill_member("kobold", "p1")
    assert state.get_tension("kobold", "goblin") == 4
    assert state.relation_band("kobold", "goblin") == "peaceful"


def test_quest_aid_vs_escalates_toward_war() -> None:
    """WHEN a player aids A against B THEN A-B tension rises by 8."""
    state = FactionState()
    initial = state.get_tension("kobold", "goblin")
    state.apply_quest_aid_vs("kobold", "goblin")
    assert state.get_tension("kobold", "goblin") == initial + 8


def test_broken_leadership_raises_rival_tension() -> None:
    """WHEN a tribe's chief and shaman die THEN tension with each rival rises by 6."""
    state = FactionState()
    initial_goblin = state.get_tension("kobold", "goblin")
    initial_orc_vol = state.get_tension("kobold", "orc_vol")
    initial_ogre = state.get_tension("kobold", "ogre")

    state.apply_leadership_broken("kobold")

    assert state.get_tension("kobold", "goblin") == initial_goblin + 6
    assert state.get_tension("kobold", "orc_vol") == initial_orc_vol + 6
    assert state.get_tension("kobold", "ogre") == initial_ogre + 6


def test_initial_relations_match_matrix() -> None:
    """WHEN a season begins THEN tribe pairs match the B2 matrix; unlisted default tense."""
    # Three highlighted set-piece pairs from §3
    assert INITIAL_RELATIONS[frozenset({"orc_vol", "orc_dec"})] == 24  # blood enemies (war)
    assert INITIAL_RELATIONS[frozenset({"goblin", "ogre"})] == -10  # ogre allied to goblins
    assert INITIAL_RELATIONS[frozenset({"goblin", "gnoll"})] == 20  # gnolls raid warren (war)

    # Verify band labels for the three set-pieces
    assert band_for(24, RELATION_LADDER) == "war"
    assert band_for(-10, RELATION_LADDER) == "allied"
    assert band_for(20, RELATION_LADDER) == "war"

    # Keep ↔ cult is war
    assert band_for(INITIAL_RELATIONS[frozenset({"keep", "cult"})], RELATION_LADDER) == "war"

    # Hobgoblin ↔ cult is peaceful (cult's first convert)
    assert (
        band_for(INITIAL_RELATIONS[frozenset({"hobgoblin", "cult"})], RELATION_LADDER) == "peaceful"
    )

    # Unlisted pair defaults to tense
    assert DEFAULT_RELATION == 12
    assert band_for(DEFAULT_RELATION, RELATION_LADDER) == "tense"


def test_decay_drifts_toward_initial_without_overshoot(monkeypatch: pytest.MonkeyPatch) -> None:
    """WHEN decay is enabled and time passes THEN values drift toward initial, never past."""
    state = FactionState()

    # Standings drift toward 0.
    state.standings[("kobold", "pos")] = 15
    state.standings[("kobold", "neg")] = -15
    state.standings[("kobold", "edge")] = -1
    state.decay_tick()
    assert state.get_standing("kobold", "pos") == 14
    assert state.get_standing("kobold", "neg") == -14
    # Edge: -1 + 1 = 0, never goes positive.
    assert state.get_standing("kobold", "edge") == 0

    # Tensions drift toward their initial value.
    # kobold-goblin initial is +10.  Set it to +12 (above) and +8 (below).
    state2 = FactionState()
    state2.tensions[("goblin", "kobold")] = 12
    state2.decay_tick()
    assert state2.tensions[("goblin", "kobold")] == 11  # drifted down by 1

    state3 = FactionState()
    state3.tensions[("goblin", "kobold")] = 8
    state3.decay_tick()
    assert state3.tensions[("goblin", "kobold")] == 9  # drifted up by 1

    # Overshoot protection: tension 1 above initial clamps to initial.
    state4 = FactionState()
    state4.tensions[("goblin", "kobold")] = 11
    monkeypatch.setattr(faction_cfg, "DECAY_PER_DAY", 5)
    state4.decay_tick()
    assert state4.tensions[("goblin", "kobold")] == 10  # clamped at initial

    # When DECAY_ENABLED is False, nothing changes.
    monkeypatch.setattr(faction_cfg, "DECAY_PER_DAY", 1)
    monkeypatch.setattr(faction_cfg, "DECAY_ENABLED", False)
    state5 = FactionState()
    state5.standings[("kobold", "still")] = -15
    state5.decay_tick()
    assert state5.get_standing("kobold", "still") == -15


def test_season_reset_clears_standing_and_reseeds_tension() -> None:
    """WHEN a season resets THEN standings clear to neutral and tension reseeds to initial."""
    state = FactionState()
    # Dirty the state.
    for _ in range(5):
        state.apply_kill_member("kobold", "p1")
    state.apply_quest_aid_vs("orc_vol", "orc_dec")

    orc_initial = INITIAL_RELATIONS[frozenset({"orc_vol", "orc_dec"})]
    assert state.get_standing("kobold", "p1") != 0
    assert state.get_tension("orc_vol", "orc_dec") != orc_initial

    state.reset_season()

    assert state.get_standing("kobold", "p1") == 0
    assert state.get_tension("orc_vol", "orc_dec") == orc_initial
    assert (
        state.get_tension("kobold", "goblin") == INITIAL_RELATIONS[frozenset({"kobold", "goblin"})]
    )


@pytest.mark.skip(reason="requires Evennia engine — lands in NPC aggression task")
def test_kill_on_sight_mob_initiates_combat() -> None:
    """WHEN a KOS-standing player enters a room with the faction's mob THEN it attacks."""


@pytest.mark.skip(reason="requires Evennia engine — lands in NPC aggression task")
def test_friendly_mob_does_not_initiate_combat() -> None:
    """WHEN a friendly-standing player enters a room with the faction's mob THEN no attack."""
