"""Phase 0 test stubs for tribe-scoped repop (R3).

Derived from openspec/changes/b2-mud-v1-design/specs/repop/spec.md and
docs/specs/repop.md §7. Docstring-only; Phase 2 unskips and implements.
"""

import pytest

pytestmark = pytest.mark.skip(reason="Phase 0 stub — implementation in Phase 2")


def test_standard_mob_respawns_after_delay() -> None:
    """WHEN a standard mob dies and STANDARD_RESPAWN elapses THEN it respawns."""


def test_killing_one_leader_does_not_halt() -> None:
    """WHEN only the chief dies THEN the tribe keeps repopping and the chief returns in 15 min."""


def test_both_leaders_dead_triggers_halt() -> None:
    """WHEN the shaman dies while the chief is dead THEN repop halts 60 min and broadcasts."""


def test_nothing_repops_during_halt() -> None:
    """WHEN a tribe is halted THEN no member, including leaders, respawns."""


def test_halt_expiry_regroups_full_tribe() -> None:
    """WHEN the halt window expires THEN the full tribe respawns with fresh leaders."""


def test_halt_raises_rival_tension() -> None:
    """WHEN a halt triggers THEN leadership_broken raises tension with each rival."""


def test_rival_scouts_spawn_in_lair() -> None:
    """WHEN a tribe is halted THEN SCOUT_PARTY_SIZE rival mobs spawn in its lair."""


def test_scouts_count_as_rival_faction() -> None:
    """WHEN a player kills a scout THEN standing changes with the rival, not the broken tribe."""


def test_scouts_retreat_on_regroup() -> None:
    """WHEN the halt expires THEN surviving scouts despawn."""


def test_shrine_resets_every_24h_with_broadcast() -> None:
    """WHEN SHRINE_RESET elapses THEN Shrine mobs respawn and a server-wide broadcast fires."""


def test_season_reset_clears_repop_state() -> None:
    """WHEN a season resets THEN all timers, halts, and scouts clear and the world rebuilds."""
