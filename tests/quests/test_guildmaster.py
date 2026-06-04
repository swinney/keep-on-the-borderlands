"""Pure-core tests for the M9 Guildmaster tribe-clearing bounty (docs/specs/quests.md §2, §9).

These exercise the catalog and the per-character state machine without booting
Evennia (no DB fixture requested). Engine wiring — the Guildmaster commands, the
kill-credit hook, the reward payout and the secure-loop tie-in — is covered by
``test_guildmaster_engine.py``.
"""

from __future__ import annotations

from world.quests import state as qstate
from world.quests.config import (
    BOUNTY_COOLDOWN_SECONDS,
    CATALOG,
    GUILDMASTER,
    KillStep,
    quests_from,
)

KOBOLD_CULL = "g_kobold_cull"


# ── catalog ─────────────────────────────────────────────────────────────────


def test_kobold_cull_is_in_the_catalog() -> None:
    quest = CATALOG[KOBOLD_CULL]
    assert quest.giver == GUILDMASTER
    assert quest.title == "Cull the Kobolds"
    assert quest.reward.gp == 50
    assert quest.harm_faction == "kobold"
    assert quest.repeatable is True


def test_kobold_cull_requires_eight_kobold_kills() -> None:
    (step,) = CATALOG[KOBOLD_CULL].steps
    assert isinstance(step, KillStep)
    assert step.faction == "kobold"
    assert step.count == 8


def test_quests_from_returns_the_guildmaster_bounty() -> None:
    offered = quests_from(GUILDMASTER)
    # The M9 kobold cull is the first Guildmaster bounty; the M13 catalog adds the
    # rest of the combat bounties, all attributed to the Guildmaster.
    assert KOBOLD_CULL in {q.id for q in offered}
    assert offered[0].id == KOBOLD_CULL
    assert all(q.giver == GUILDMASTER for q in offered)
    assert quests_from("nobody") == []


# ── progress / completion ────────────────────────────────────────────────────


def test_fresh_progress_is_zeroed_per_faction() -> None:
    quest = CATALOG[KOBOLD_CULL]
    assert qstate.fresh_progress(quest) == {"kobold": 0}


def test_steps_met_flips_only_at_the_required_count() -> None:
    quest = CATALOG[KOBOLD_CULL]
    assert not qstate.steps_met(quest, {"kobold": 7})
    assert qstate.steps_met(quest, {"kobold": 8})
    assert qstate.steps_met(quest, {"kobold": 9})


def test_remaining_counts_down_and_never_negative() -> None:
    quest = CATALOG[KOBOLD_CULL]
    assert qstate.remaining(quest, {"kobold": 0}) == {"kobold": 8}
    assert qstate.remaining(quest, {"kobold": 3}) == {"kobold": 5}
    assert qstate.remaining(quest, {"kobold": 12}) == {"kobold": 0}


def test_credit_kill_increments_and_caps_at_step_count() -> None:
    quest = CATALOG[KOBOLD_CULL]
    progress = qstate.credit_kill(quest, {"kobold": 0}, "kobold")
    assert progress == {"kobold": 1}
    assert qstate.credit_kill(quest, {"kobold": 8}, "kobold") == {"kobold": 8}


def test_credit_kill_ignores_unrelated_factions() -> None:
    quest = CATALOG[KOBOLD_CULL]
    assert qstate.credit_kill(quest, {"kobold": 2}, "orc_vol") == {"kobold": 2}


# ── state machine: availability / accept / turn-in ───────────────────────────


def test_unseen_quest_is_available_when_level_met() -> None:
    quest = CATALOG[KOBOLD_CULL]
    assert qstate.status(quest, None, level=1, now=0.0) == qstate.AVAILABLE
    assert qstate.can_accept(quest, None, level=1, now=0.0)


def test_accept_sets_active_and_preserves_history() -> None:
    quest = CATALOG[KOBOLD_CULL]
    entry = qstate.accept(quest, None)
    assert entry["state"] == qstate.ACTIVE
    assert entry["progress"] == {"kobold": 0}
    assert entry["times_completed"] == 0

    prior: qstate.QuestEntry = {
        "state": qstate.COMPLETE,
        "progress": {"kobold": 8},
        "times_completed": 2,
        "cooldown_until": 0.0,
    }
    reaccepted = qstate.accept(quest, prior)
    assert reaccepted["state"] == qstate.ACTIVE
    assert reaccepted["progress"] == {"kobold": 0}
    assert reaccepted["times_completed"] == 2


def test_turn_in_marks_complete_bumps_history_and_arms_cooldown() -> None:
    quest = CATALOG[KOBOLD_CULL]
    entry: qstate.QuestEntry = {
        "state": qstate.ACTIVE,
        "progress": {"kobold": 8},
        "times_completed": 0,
        "cooldown_until": 0.0,
    }
    done = qstate.turn_in(quest, entry, now=1000.0)
    assert done["state"] == qstate.COMPLETE
    assert done["times_completed"] == 1
    assert done["cooldown_until"] == 1000.0 + BOUNTY_COOLDOWN_SECONDS


def test_repeatable_bounty_reopens_after_cooldown() -> None:
    quest = CATALOG[KOBOLD_CULL]
    completed: qstate.QuestEntry = {
        "state": qstate.COMPLETE,
        "progress": {"kobold": 8},
        "times_completed": 1,
        "cooldown_until": 1000.0,
    }
    # Still cooling down → stays complete and cannot be re-accepted.
    assert qstate.status(quest, completed, level=1, now=999.0) == qstate.COMPLETE
    assert not qstate.can_accept(quest, completed, level=1, now=999.0)
    # Cooldown elapsed → available again.
    assert qstate.status(quest, completed, level=1, now=1000.0) == qstate.AVAILABLE
    assert qstate.can_accept(quest, completed, level=1, now=1000.0)


# ── log-level crediting (the mob-death hook's pure half) ──────────────────────


def test_record_faction_kill_advances_only_active_quests() -> None:
    log: qstate.QuestLog = {KOBOLD_CULL: qstate.accept(CATALOG[KOBOLD_CULL], None)}
    assert qstate.record_faction_kill(log, CATALOG, "kobold") is True
    assert log[KOBOLD_CULL]["progress"] == {"kobold": 1}


def test_record_faction_kill_ignores_completed_and_unrelated() -> None:
    log: qstate.QuestLog = {
        KOBOLD_CULL: {
            "state": qstate.COMPLETE,
            "progress": {"kobold": 8},
            "times_completed": 1,
            "cooldown_until": 0.0,
        }
    }
    # Completed quest does not progress.
    assert qstate.record_faction_kill(log, CATALOG, "kobold") is False

    log[KOBOLD_CULL] = qstate.accept(CATALOG[KOBOLD_CULL], None)
    # An active quest still ignores a faction it does not track.
    assert qstate.record_faction_kill(log, CATALOG, "orc_vol") is False
    assert log[KOBOLD_CULL]["progress"] == {"kobold": 0}
