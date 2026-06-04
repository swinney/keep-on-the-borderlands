"""XP-pacing projection tests (acceptance.md §6.2-§6.3, M16 slice 1).

Pure / Django-free: these exercise ``world.rules.pacing`` over the existing pure
cores with no Evennia boot. They pin the deterministic projection of the
representative play arc (so a pacing-knob regression is caught) and assert the
OSE XP table is untouched (pacing is balanced via the economy/arc knobs, not by
rewriting the SRD canon — acceptance.md §3.3).
"""

from __future__ import annotations

from world.rules.economy import secure_xp
from world.rules.pacing import (
    REPRESENTATIVE_CLASS,
    TARGET_LEVEL_BAND,
    Arc,
    ArcResult,
    project_arc,
)
from world.rules.progression import level_for_xp, xp_for_level
from world.rules.saves import CharacterClass

# The canonical OSE Fighter thresholds for the band boundaries (progression.py /
# SRD). Referenced here, never redefined — if pacing balancing ever silently
# edited the SRD table, behavior 3 below would fail.
_FIGHTER_L9_XP = 240000
_FIGHTER_L10_XP = 360000


# ── behavior 1: the representative arc lands in the target band (§3.1, §6.2) ──


def test_representative_arc_reaches_target_band() -> None:
    """The representative class reaches ~L10 (the L9-L10 band) over the season."""
    result = project_arc(REPRESENTATIVE_CLASS)
    low, high = TARGET_LEVEL_BAND
    assert low <= result.final_level <= high
    # The final level is resolved by the unmodified OSE table, not asserted ad hoc.
    assert result.final_level == level_for_xp(REPRESENTATIVE_CLASS, result.total_xp)


def test_target_band_is_l9_l10() -> None:
    """The documented target band is L9-L10 (acceptance.md §3.1)."""
    assert TARGET_LEVEL_BAND == (9, 10)


# ── behavior 2: the projection is deterministic and curve-pinned (§6.2) ──────


def test_projection_is_deterministic() -> None:
    """Same inputs → same result (no RNG in the projection — §3.2)."""
    assert project_arc(REPRESENTATIVE_CLASS) == project_arc(REPRESENTATIVE_CLASS)


def test_weekly_curve_is_pinned() -> None:
    """Pin the full projected curve as a regression guard on the pacing knobs.

    A change to any pacing/economy knob that feeds the arc shifts these numbers,
    breaking this test — the balance is regression-guarded (acceptance.md §3.3).
    """
    result = project_arc(REPRESENTATIVE_CLASS)
    assert result == ArcResult(
        total_xp=280800,
        final_level=9,
        weekly_xp=(46800, 93600, 140400, 187200, 234000, 280800),
        weekly_levels=(6, 7, 8, 8, 8, 9),
    )
    # One entry per week of the 6-week season.
    assert len(result.weekly_xp) == 6
    assert len(result.weekly_levels) == 6


def test_total_xp_matches_closed_form_arc_sum() -> None:
    """total_xp == weeks·encounters·(secured_gp + kill_xp): secure_xp credits
    every secured gp exactly once, so the treasure XP equals the secured total."""
    arc = Arc()
    expected = (
        arc.weeks
        * arc.encounters_per_week
        * (arc.avg_secured_gp_per_clear + arc.avg_kill_xp_per_clear)
    )
    assert project_arc(REPRESENTATIVE_CLASS, arc).total_xp == expected


# ── behavior 3: the OSE XP table is untouched (§6.3) ─────────────────────────


def test_ose_xp_table_untouched() -> None:
    """Pacing tuning must not retune the SRD XP thresholds (acceptance.md §3.3).

    Referenced against the canonical band-boundary values, not a redefined table.
    """
    assert xp_for_level(CharacterClass.FIGHTER, 9) == _FIGHTER_L9_XP
    assert xp_for_level(CharacterClass.FIGHTER, 10) == _FIGHTER_L10_XP
    # The band boundaries behave as the table dictates.
    assert level_for_xp(CharacterClass.FIGHTER, _FIGHTER_L9_XP) == 9
    assert level_for_xp(CharacterClass.FIGHTER, _FIGHTER_L10_XP) == 10
    assert level_for_xp(CharacterClass.FIGHTER, _FIGHTER_L9_XP - 1) == 8


def test_projection_composes_secure_xp_unchanged() -> None:
    """The model uses economy.secure_xp as-is: re-securing grants nothing.

    A single clear's treasure, secured then re-secured, credits its gp once —
    the property project_arc relies on.
    """
    grant_first, credited = secure_xp(6000, 0)
    grant_again, _ = secure_xp(6000, credited)
    assert grant_first == 6000
    assert grant_again == 0
