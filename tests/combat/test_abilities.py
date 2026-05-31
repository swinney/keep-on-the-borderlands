"""Contract for ability scores and modifiers (M1).

Derived from docs/specs/combat.md §1 (the OSE modifier table) and §3 (HP).
"""

import random

import pytest

from world.rules import abilities, progression

# ── ability modifier table (docs/specs/combat.md §1) ─────────────────────────


@pytest.mark.parametrize(
    ("score", "modifier"),
    [
        (3, -3),
        (4, -2),
        (5, -2),
        (6, -1),
        (7, -1),
        (8, -1),
        (9, 0),
        (10, 0),
        (11, 0),
        (12, 0),
        (13, 1),
        (14, 1),
        (15, 1),
        (16, 2),
        (17, 2),
        (18, 3),
    ],
)
def test_ability_modifier_table(score: int, modifier: int) -> None:
    """WHEN a score is 3/9/13/18 THEN modifier is -3/0/+1/+3 (full OSE table)."""
    assert abilities.ability_modifier(score) == modifier


@pytest.mark.parametrize("bad", [2, 19, 0, -1, 100])
def test_ability_modifier_rejects_out_of_range(bad: int) -> None:
    """WHEN a score is outside the OSE 3-18 range THEN ValueError is raised."""
    with pytest.raises(ValueError):
        abilities.ability_modifier(bad)


# ── score generation: 3d6 in order ──────────────────────────────────────────


def test_roll_ability_scores_are_all_in_range() -> None:
    """WHEN scores are rolled THEN all six are 3d6 results in [3, 18]."""
    scores = abilities.roll_ability_scores(rng=random.Random(1))
    assert all(3 <= value <= 18 for value in scores.as_dict().values())


def test_roll_ability_scores_is_reproducible() -> None:
    """WHEN two rolls share a seed THEN the generated scores are identical."""
    assert abilities.roll_ability_scores(rng=random.Random(7)) == abilities.roll_ability_scores(
        rng=random.Random(7)
    )


# ── hit points (docs/specs/combat.md §3) ─────────────────────────────────────


def test_hp_per_level_floors_at_one() -> None:
    """WHEN HD roll plus negative CON mod is below 1 THEN HP gained is 1."""
    for seed in range(50):
        assert progression.roll_hit_points(hit_die=4, con_modifier=-3, rng=random.Random(seed)) >= 1


def test_hp_per_level_stays_within_bounds() -> None:
    """WHEN rolling a d8 with +1 CON THEN HP gained is in [2, 9]."""
    rng = random.Random(3)
    for _ in range(500):
        assert 2 <= progression.roll_hit_points(hit_die=8, con_modifier=1, rng=rng) <= 9
