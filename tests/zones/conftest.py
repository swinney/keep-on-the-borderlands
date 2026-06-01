"""Fixtures for zone engine tests (requires pytest-django / Evennia).

Pure-data zone tests (test_keep.py) request no DB fixture and so never trigger
this bootstrap; only the build-time tests (test_keep_build.py) do.
"""

from typing import Any

import evennia
import pytest


@pytest.fixture(scope="session", autouse=True)
def _bootstrap_evennia_zones(django_db_setup: Any, django_db_blocker: Any) -> None:
    """Initialise the Evennia API once per session for zone tests."""
    with django_db_blocker.unblock():
        # Other engine suites share this flag so _init runs at most once.
        if not getattr(evennia, "_kotb_initialized", False):
            evennia._init()
            evennia._kotb_initialized = True
