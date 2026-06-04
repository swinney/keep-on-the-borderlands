"""XP-pacing projection (pure) — docs/specs/acceptance.md §3.

A deterministic balance projection: does a representative player following the
campaign's intended clear-and-bank loop reach roughly level 10 over a 6-week
season (CLAUDE.md §2: B2 level range 1-10, 6-week seasons)?

This is a *projection*, not a simulation or a playtest (acceptance.md §3.4): it
uses expected values, no RNG, so the result is exact and reproducible and a
pacing test can pin it as a regression guard. It composes the existing pure
cores unchanged — ``economy.secure_xp`` for the treasure-as-XP link
(economy.md §6) and ``progression.level_for_xp`` for the OSE level lookup — and
never re-derives or retunes them. No Evennia import (CLAUDE.md §3, architecture
§1).

The model's assumptions are the named constants below; they are what a reviewer
scrutinizes (acceptance.md §3.2-§3.3). The OSE XP thresholds in ``progression``
are SRD canon and are **not** tuned here; pacing is balanced via the economy
knobs and these arc constants (acceptance.md §3.3).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from world.rules.economy import secure_xp
from world.rules.progression import level_for_xp
from world.rules.saves import CharacterClass

# ---------------------------------------------------------------------------
# §3.2 the representative play arc — named assumptions, grounded in the wired
# M9-M13 content. A "clear" is one secured tribe-lair/quest loop: the party
# clears a Caves of Chaos lair (or completes the equivalent quest chain), banks
# the recovered hoard, and is credited the kill XP of the monsters slain.
#
#   - avg_secured_gp_per_clear: the OSE tribe-lair coin/gem hoard secured to the
#     bank per clear (economy.md §6: 1 gp secured = 1 XP). This is the campaign's
#     primary XP source. The M13 quest bounties (config gp rewards span 30-1000,
#     mean ~190) are a smaller, additive slice folded into this figure; the bulk
#     is the lair treasure hoards that B2/OSE tribe caves carry.
#   - avg_kill_xp_per_clear: the summed OSE XP-by-HD award for the tribe of
#     monsters slain in one lair clear (additive to treasure XP; combat spec).
#   - encounters_per_week: secured clears an engaged player completes per week,
#     across a 6-week season with tribe-scoped repop (repop.md) refreshing lairs.
# ---------------------------------------------------------------------------
SEASON_WEEKS = 6  # CLAUDE.md §2: 6-week seasons (locked).
ENCOUNTERS_PER_WEEK = 6
AVG_SECURED_GP_PER_CLEAR = 6000
AVG_KILL_XP_PER_CLEAR = 1800

# §3.1 the representative class and the target band the projection must land in.
# Fighter is the canonical B2 front-liner; L9-L10 is "roughly level 10" — the
# cap is reachable (not too slow) but not trivially hit (not too fast).
REPRESENTATIVE_CLASS = CharacterClass.FIGHTER
TARGET_LEVEL_BAND = (9, 10)


@dataclass(frozen=True)
class Arc:
    """A parameterized representative play arc (acceptance.md §3.2).

    Defaults are the module's named assumptions; a test or a what-if analysis
    may override any field. ``weeks`` and ``encounters_per_week`` shape the
    schedule; the two ``avg_*`` fields are the per-clear XP yields.
    """

    weeks: int = SEASON_WEEKS
    encounters_per_week: int = ENCOUNTERS_PER_WEEK
    avg_secured_gp_per_clear: int = AVG_SECURED_GP_PER_CLEAR
    avg_kill_xp_per_clear: int = AVG_KILL_XP_PER_CLEAR


# The default representative arc — a frozen (immutable) singleton, safe to share
# as ``project_arc``'s default argument.
REPRESENTATIVE_ARC = Arc()


@dataclass(frozen=True)
class ArcResult:
    """The outcome of projecting an arc for a class (acceptance.md §3.2).

    ``total_xp`` is the accumulated XP at season end; ``final_level`` is the
    attained level. ``weekly_xp``/``weekly_levels`` are the cumulative XP and
    attained level at the end of each week (length == ``arc.weeks``) — the
    per-week curve the pacing test pins as a regression guard.
    """

    total_xp: int
    final_level: int
    weekly_xp: tuple[int, ...] = field(default_factory=tuple)
    weekly_levels: tuple[int, ...] = field(default_factory=tuple)


def project_arc(char_class: CharacterClass, arc: Arc = REPRESENTATIVE_ARC) -> ArcResult:
    """Project the level a representative ``char_class`` reaches over ``arc``.

    Deterministic (expected values, no RNG): the same inputs always yield the
    same result. Each clear secures ``arc.avg_secured_gp_per_clear`` gp — run
    through ``economy.secure_xp`` so the treasure-as-XP accounting is the real
    one (each gp credited exactly once) — plus a flat
    ``arc.avg_kill_xp_per_clear`` kill XP. Level is resolved by the unmodified
    OSE table via ``progression.level_for_xp``.
    """
    total_xp = 0
    secured_running = 0
    credited = 0
    weekly_xp: list[int] = []
    weekly_levels: list[int] = []

    for _week in range(arc.weeks):
        for _clear in range(arc.encounters_per_week):
            secured_running += arc.avg_secured_gp_per_clear
            grant, credited = secure_xp(secured_running, credited)
            total_xp += grant + arc.avg_kill_xp_per_clear
        weekly_xp.append(total_xp)
        weekly_levels.append(level_for_xp(char_class, total_xp))

    return ArcResult(
        total_xp=total_xp,
        final_level=level_for_xp(char_class, total_xp),
        weekly_xp=tuple(weekly_xp),
        weekly_levels=tuple(weekly_levels),
    )
