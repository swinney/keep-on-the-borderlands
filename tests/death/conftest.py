"""Fixtures for death engine tests (requires pytest-django / Evennia)."""

from typing import Any

import evennia
import pytest


@pytest.fixture(scope="session", autouse=True)
def _bootstrap_evennia_death(django_db_setup: Any, django_db_blocker: Any) -> None:
    """Initialise the Evennia API once per session for death tests."""
    with django_db_blocker.unblock():
        evennia._init()
