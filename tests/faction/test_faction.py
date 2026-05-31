"""Tests for the faction system (R2).

Derived from openspec/changes/b2-mud-v1-design/specs/faction-system/spec.md and
docs/specs/faction.md §7.

Config-level tests (band_for, initial matrix) are active.  Tests that require
the faction_manager GlobalScript (event processing, decay, season reset, NPC
binding) are individually skipped until those tasks land.
"""

import pytest

from world.factions.config import (
    DEFAULT_RELATION,
    INITIAL_RELATIONS,
    RELATION_LADDER,
    STANDING_LADDER,
    band_for,
)


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


@pytest.mark.skip(reason="requires faction_manager — lands in next task")
def test_five_kills_make_standing_hostile() -> None:
    """WHEN a player kills five faction members THEN standing is hostile (R=-15)."""


@pytest.mark.skip(reason="requires faction_manager — lands in next task")
def test_ten_kills_make_standing_kill_on_sight() -> None:
    """WHEN a player kills ten faction members THEN standing is kill-on-sight (R=-30)."""


@pytest.mark.skip(reason="requires faction_manager — lands in next task")
def test_killing_leader_costs_eight() -> None:
    """WHEN a player kills a chief or shaman THEN reputation drops by 8."""


@pytest.mark.skip(reason="requires faction_manager — lands in next task")
def test_quest_aid_and_harm_move_standing_by_ten() -> None:
    """WHEN a player completes an aiding/harming quest THEN standing moves +/-10."""


@pytest.mark.skip(reason="requires faction_manager — lands in next task")
def test_bribe_cannot_exceed_neutral() -> None:
    """WHEN a player bribes past +15 THEN standing rises no higher than neutral."""


@pytest.mark.skip(reason="requires faction_manager — lands in next task")
def test_killing_members_thaws_only_tense_or_war_rivals() -> None:
    """WHEN a player kills faction members THEN tension drops only with tense/war rivals."""


@pytest.mark.skip(reason="requires faction_manager — lands in next task")
def test_kobold_goblin_crosses_tense_to_peaceful() -> None:
    """WHEN enough kobolds die THEN kobold-goblin relation becomes peaceful."""


@pytest.mark.skip(reason="requires faction_manager — lands in next task")
def test_quest_aid_vs_escalates_toward_war() -> None:
    """WHEN a player aids A against B THEN A-B tension rises by 8."""


@pytest.mark.skip(reason="requires faction_manager — lands in next task")
def test_broken_leadership_raises_rival_tension() -> None:
    """WHEN a tribe's chief and shaman die THEN tension with each rival rises by 6."""


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


@pytest.mark.skip(reason="requires faction_manager — lands in next task")
def test_decay_drifts_toward_initial_without_overshoot() -> None:
    """WHEN decay is enabled and time passes THEN values drift toward initial, never past."""


@pytest.mark.skip(reason="requires faction_manager — lands in next task")
def test_season_reset_clears_standing_and_reseeds_tension() -> None:
    """WHEN a season resets THEN standings clear to neutral and tension reseeds to initial."""


@pytest.mark.skip(reason="requires Evennia engine — lands in NPC aggression task")
def test_kill_on_sight_mob_initiates_combat() -> None:
    """WHEN a KOS-standing player enters a room with the faction's mob THEN it attacks."""


@pytest.mark.skip(reason="requires Evennia engine — lands in NPC aggression task")
def test_friendly_mob_does_not_initiate_combat() -> None:
    """WHEN a friendly-standing player enters a room with the faction's mob THEN no attack."""
