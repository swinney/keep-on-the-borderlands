"""Fixtures for death engine tests (requires pytest-django / Evennia)."""

from typing import Any

import evennia
import pytest


@pytest.fixture(scope="session", autouse=True)
def _bootstrap_evennia_death(django_db_setup: Any, django_db_blocker: Any) -> None:
    """Initialise the Evennia API once per session for death tests."""
    with django_db_blocker.unblock():
        # The engine suite has an equivalent autouse fixture; share a flag so
        # whichever runs first initialises and the other is a no-op (_init is
        # not guaranteed idempotent).
        if not getattr(evennia, "_kotb_initialized", False):
            evennia._init()
            evennia._kotb_initialized = True
