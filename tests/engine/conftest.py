"""Fixtures shared by engine (pytest-django) tests.

Only suites under ``tests/engine/`` pull in this autouse fixture, so the pure
rules tests (``tests/combat/`` etc.) never pay the database-setup cost — they
run Django-free even though ``DJANGO_SETTINGS_MODULE`` is configured globally.
"""

from typing import Any

import evennia
import pytest


@pytest.fixture(scope="session", autouse=True)
def _bootstrap_evennia(django_db_setup: Any, django_db_blocker: Any) -> None:
    """Initialise the Evennia API once per session.

    Mirrors what Evennia's own ``DiscoverRunner`` does in
    ``setup_test_environment`` (``evennia._init()``); ``pytest-django`` has
    already run ``django.setup()`` by the time this fixture is resolved. The DB
    blocker is lifted because ``_init`` touches ``ServerConfig`` during startup.
    """
    with django_db_blocker.unblock():
        evennia._init()
