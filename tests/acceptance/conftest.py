"""Fixtures for acceptance engine tests (requires pytest-django / Evennia).

The XP-pacing projection tests (``test_xp_pacing.py``) are pure and request no DB
fixture; the C8 latency measurement (``test_latency_50.py``) marks
``@pytest.mark.django_db`` and relies on this session bootstrap, mirroring
``tests/world_build/conftest.py`` and ``tests/zones/conftest.py``.
"""

from typing import Any

import evennia
import pytest


@pytest.fixture(scope="session", autouse=True)
def _bootstrap_evennia_acceptance(django_db_setup: Any, django_db_blocker: Any) -> None:
    """Initialise the Evennia API once per session for acceptance engine tests."""
    with django_db_blocker.unblock():
        # Other engine suites share this flag so _init runs at most once.
        if not getattr(evennia, "_kotb_initialized", False):
            evennia._init()
            evennia._kotb_initialized = True
