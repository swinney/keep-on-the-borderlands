"""Fixtures for economy engine tests (requires pytest-django / Evennia)."""

from typing import Any

import evennia
import pytest


@pytest.fixture(scope="session", autouse=True)
def _bootstrap_evennia_economy(django_db_setup: Any, django_db_blocker: Any) -> None:
    """Initialise the Evennia API once per session for economy command tests."""
    with django_db_blocker.unblock():
        if not getattr(evennia, "_kotb_initialized", False):
            evennia._init()
            evennia._kotb_initialized = True
