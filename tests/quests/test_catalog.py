"""Pure-core tests for the full M13 quest catalog (docs/specs/quests.md §1-§8).

These assert the *data* the M13 "wire all 24 quests across givers" task lands: the
catalog holds every enumerated quest, attributed to the right giver, with the
prerequisite and cross-system-effect fields the §2-§7 tables specify. The behaviour
that *acts* on this data (prereq enforcement, effect firing) belongs to later M13
slices and the managers; here we only pin the catalog itself.

The quests are exercised without booting Evennia (no DB fixture requested).
"""

from __future__ import annotations

import pytest

from world.quests import state as qstate
from world.quests.config import (
    CASTELLAN,
    CATALOG,
    CATALOG_IDS,
    CURATE,
    EVIDENCE_CURATE,
    EVIDENCE_REPORT,
    GIVERS,
    GOBLIN_CHIEF,
    GUILDMASTER,
    HERMIT,
    ORC_DEC_CHIEF,
    ORC_VOL_CHIEF,
    PROVISIONER,
    SEASON_END_SEASON,
    SEASON_EXPOSE_PRIEST,
    SPY,
    DeedStep,
    KillStep,
    Quest,
    quests_from,
)

# The §2-§7 tables, grouped by giver. The prose summary says "24"; the tables
# enumerate 26 distinct ids (see config.py count note). These are the contract.
EXPECTED_BY_GIVER: dict[str, list[str]] = {
    GUILDMASTER: [
        "g_kobold_cull",
        "g_orc_vile",
        "g_orc_dec",
        "g_bugbear_chief",
        "g_gnoll_chief",
        "g_hobgoblin_king",
        "g_owlbear",
        "g_minotaur",
    ],
    CASTELLAN: [
        "c_scout_caves",
        "c_rescue_soldier",
        "c_expose_priest",
        "c_destroy_shrine",
    ],
    CURATE: ["cu_holy_water", "cu_suspicions", "cu_bless_blades"],
    PROVISIONER: ["p_caravan", "p_supplies"],
    HERMIT: ["h_rare_herb", "h_lions"],
    ORC_VOL_CHIEF: ["t_vol_vs_dec"],
    ORC_DEC_CHIEF: ["t_dec_vs_vol"],
    GOBLIN_CHIEF: ["t_gob_vs_gnoll", "t_bribe_ogre"],
    SPY: ["sp_package", "sp_reagent", "sp_minister"],
}

ALL_EXPECTED_IDS = [qid for ids in EXPECTED_BY_GIVER.values() for qid in ids]


# ── catalog completeness & giver attribution ─────────────────────────────────


def test_catalog_holds_every_enumerated_quest() -> None:
    assert set(CATALOG) == set(ALL_EXPECTED_IDS)
    # 26 distinct ids enumerated across the §2-§7 tables.
    assert len(CATALOG) == len(ALL_EXPECTED_IDS) == 26


def test_catalog_ids_view_matches_catalog_order() -> None:
    assert tuple(CATALOG) == CATALOG_IDS


def test_every_giver_in_GIVERS_offers_at_least_one_quest() -> None:
    for giver in GIVERS:
        assert quests_from(giver), f"{giver} offers no quests"
    assert set(GIVERS) == set(EXPECTED_BY_GIVER)


def test_quests_from_groups_each_quest_under_its_giver() -> None:
    for giver, expected_ids in EXPECTED_BY_GIVER.items():
        assert [q.id for q in quests_from(giver)] == expected_ids


def test_every_quest_giver_field_is_a_known_giver() -> None:
    for quest in CATALOG.values():
        assert quest.giver in GIVERS


def test_unknown_giver_offers_nothing() -> None:
    assert quests_from("nobody") == []


def test_every_quest_has_at_least_one_step_and_a_reward() -> None:
    for quest in CATALOG.values():
        assert quest.steps, f"{quest.id} has no steps"
        assert isinstance(quest.reward.gp, int)


# ── repeatable vs story (quests.md §1, §2) ───────────────────────────────────


def test_only_guildmaster_bounties_are_repeatable() -> None:
    for quest in CATALOG.values():
        if quest.giver == GUILDMASTER:
            assert quest.repeatable, f"{quest.id} should be a repeatable bounty"
        else:
            assert not quest.repeatable, f"{quest.id} is a story quest, not repeatable"


# ── prerequisites (quests.md §1, §3, §5, §7) ─────────────────────────────────


def test_level_prereqs_match_the_tables() -> None:
    assert CATALOG["g_orc_vile"].min_level == 2
    assert CATALOG["g_bugbear_chief"].min_level == 3
    assert CATALOG["g_hobgoblin_king"].min_level == 4
    assert CATALOG["g_minotaur"].min_level == 5
    assert CATALOG["c_destroy_shrine"].min_level == 7


def test_quest_chains_declare_their_prior_quest() -> None:
    assert CATALOG["sp_reagent"].prereq_quests == ("sp_package",)
    assert CATALOG["sp_minister"].prereq_quests == ("sp_reagent",)
    assert CATALOG["h_rare_herb"].prereq_quests == ("p_supplies",)
    assert CATALOG["c_destroy_shrine"].prereq_quests == ("g_minotaur",)


def test_tribe_chief_quests_gate_on_non_hostile_standing() -> None:
    for qid in ("t_vol_vs_dec", "t_dec_vs_vol", "t_gob_vs_gnoll", "t_bribe_ogre"):
        gates = CATALOG[qid].standing_gates
        assert len(gates) == 1
        assert gates[0].min_band == "neutral"
    # Each chief gates on standing with its own tribe.
    assert CATALOG["t_vol_vs_dec"].standing_gates[0].faction == "orc_vol"
    assert CATALOG["t_dec_vs_vol"].standing_gates[0].faction == "orc_dec"
    assert CATALOG["t_gob_vs_gnoll"].standing_gates[0].faction == "goblin"


def test_evidence_gated_quests_declare_their_grade() -> None:
    # The two evidence-gated quests carry distinct grades (R4 §3): exposing the
    # spy needs report-grade proof, the Curate's doubt opens at the lower bar.
    assert CATALOG["c_expose_priest"].evidence_min == EVIDENCE_REPORT
    assert CATALOG["cu_suspicions"].evidence_min == EVIDENCE_CURATE
    # Every other quest is ungated.
    gated = {qid for qid, q in CATALOG.items() if q.evidence_min is not None}
    assert gated == {"c_expose_priest", "cu_suspicions"}


# ── completion effects (quests.md §8) ────────────────────────────────────────


def test_harm_and_aid_factions_match_the_tables() -> None:
    assert CATALOG["g_kobold_cull"].harm_faction == "kobold"
    assert CATALOG["p_caravan"].harm_faction == "bugbear"
    assert CATALOG["c_rescue_soldier"].aid_faction == "keep"


def test_tribe_quests_escalate_the_right_pair() -> None:
    assert CATALOG["t_vol_vs_dec"].tension_pair == ("orc_vol", "orc_dec")
    assert CATALOG["t_dec_vs_vol"].tension_pair == ("orc_dec", "orc_vol")
    assert CATALOG["t_gob_vs_gnoll"].tension_pair == ("goblin", "gnoll")
    assert CATALOG["t_vol_vs_dec"].aid_faction == "orc_vol"
    assert CATALOG["t_dec_vs_vol"].aid_faction == "orc_dec"


def test_bribe_ogre_breaks_the_goblin_ogre_alliance() -> None:
    quest = CATALOG["t_bribe_ogre"]
    assert quest.breaks_alliance == ("goblin", "ogre")
    assert quest.tension_pair is None


def test_spy_chain_is_flagged_aids_cult() -> None:
    for qid in ("sp_package", "sp_reagent", "sp_minister"):
        assert CATALOG[qid].aids_cult is True
        assert CATALOG[qid].giver == SPY
    # Nothing outside the spy chain aids the cult.
    non_spy = [q.id for q in CATALOG.values() if q.aids_cult and q.giver != SPY]
    assert non_spy == []


def test_season_global_quests_carry_the_right_tag() -> None:
    assert CATALOG["c_expose_priest"].season_global == SEASON_EXPOSE_PRIEST
    assert CATALOG["c_destroy_shrine"].season_global == SEASON_END_SEASON
    # Exactly these two quests are season-global (quests.md §8).
    globals_ = {q.id for q in CATALOG.values() if q.season_global is not None}
    assert globals_ == {"c_expose_priest", "c_destroy_shrine"}


def test_season_global_quests_grant_their_reward_item() -> None:
    assert CATALOG["c_expose_priest"].reward.gp == 250
    assert CATALOG["c_expose_priest"].reward.items
    assert CATALOG["c_destroy_shrine"].reward.gp == 1000
    assert "a holy relic" in CATALOG["c_destroy_shrine"].reward.items


# ── step shapes & state-machine tolerance of deeds (quests.md §1) ────────────


def test_chief_kill_steps_name_their_target() -> None:
    (step,) = CATALOG["g_orc_vile"].steps
    assert isinstance(step, KillStep)
    assert step.faction == "orc_vol"
    assert step.count == 1
    assert step.target == "orc_vol_chief"


def test_kill_step_count_bounties_have_no_named_target() -> None:
    (step,) = CATALOG["t_vol_vs_dec"].steps
    assert isinstance(step, KillStep)
    assert step.faction == "orc_dec"
    assert step.count == 6
    assert step.target is None


def test_deed_quests_carry_no_kill_progress() -> None:
    quest = CATALOG["c_expose_priest"]
    (step,) = quest.steps
    assert isinstance(step, DeedStep)
    # A pure deed has nothing for the kill-tracker to count.
    assert qstate.kill_steps(quest) == ()
    assert qstate.fresh_progress(quest) == {}
    # ...so the kill-tracker reports it vacuously "met"; the engine deed gates it.
    assert qstate.steps_met(quest, {}) is True


def test_state_machine_still_tracks_a_kill_quest_end_to_end() -> None:
    quest = CATALOG["t_dec_vs_vol"]  # kill 6 orc_vol
    entry = qstate.accept(quest, None)
    assert entry["progress"] == {"orc_vol": 0}
    progress = entry["progress"]
    for _ in range(6):
        progress = qstate.credit_kill(quest, progress, "orc_vol")
    assert progress == {"orc_vol": 6}
    assert qstate.steps_met(quest, progress)
    # Credit never exceeds the required count.
    assert qstate.credit_kill(quest, progress, "orc_vol") == {"orc_vol": 6}


def test_quest_dataclass_is_frozen() -> None:
    quest: Quest = CATALOG["g_kobold_cull"]
    with pytest.raises((AttributeError, TypeError)):
        quest.title = "tampered"  # type: ignore[misc]
