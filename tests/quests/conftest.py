"""Fixtures for quest engine tests (requires pytest-django / Evennia).

Pure-core tests (test_guildmaster.py) request no DB fixture and so never trigger
this bootstrap; only the engine tests (test_guildmaster_engine.py) do.
"""

from typing import Any

import evennia
import pytest


@pytest.fixture(scope="session", autouse=True)
def _bootstrap_evennia_quests(django_db_setup: Any, django_db_blocker: Any) -> None:
    """Initialise the Evennia API once per session for quest engine tests."""
    with django_db_blocker.unblock():
        # Other engine suites share this flag so _init runs at most once.
        if not getattr(evennia, "_kotb_initialized", False):
            evennia._init()
            evennia._kotb_initialized = True
