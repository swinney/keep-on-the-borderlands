"""Engine tests for the PriestManager GlobalScript rotation (M12).

Covers docs/specs/disguised-priest.md §2/§6 and testable behaviors 1-2: the
manager seeds a spy on creation and re-rolls it each season without repeating
the outgoing identity. The rotation arithmetic itself is exercised purely in
tests/disguised_priest/; here we confirm the persisted manager honours it.
"""

from __future__ import annotations

from random import Random

import pytest
from evennia.utils import create

from world.priest import config as cfg


@pytest.mark.django_db
def test_manager_seeds_a_spy_on_creation() -> None:
    """WHEN the manager is created THEN exactly one pool NPC is the spy."""
    mgr = create.create_script("world.managers.priest_manager.PriestManager")
    try:
        assert mgr.spy_id in cfg.POOL_IDS
    finally:
        mgr.delete()


@pytest.mark.django_db
def test_manager_reset_never_repeats_spy() -> None:
    """WHEN the manager resets each season THEN the spy never repeats back-to-back."""
    mgr = create.create_script("world.managers.priest_manager.PriestManager")
    try:
        rng = Random(20260604)
        previous = mgr.spy_id
        for _ in range(50):
            mgr.reset_season(rng)
            assert mgr.spy_id != previous
            assert mgr.spy_id in cfg.POOL_IDS
            previous = mgr.spy_id
    finally:
        mgr.delete()
