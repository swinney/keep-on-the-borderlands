"""Fixtures for seasonal-reset engine tests (requires pytest-django / Evennia).

Only the engine-level persistence check (behavior 3) needs a booted Evennia;
the pure-core tests in this suite run Django-free. The autouse fixture mirrors
tests/engine/ and tests/death/: it initialises the Evennia API once per session
and shares the ``_kotb_initialized`` flag so whichever suite runs first does the
work and the others are a no-op (``_init`` is not guaranteed idempotent).
"""

from typing import Any

import evennia
import pytest


@pytest.fixture(scope="session", autouse=True)
def _bootstrap_evennia_seasonal(django_db_setup: Any, django_db_blocker: Any) -> None:
    """Initialise the Evennia API once per session for seasonal-reset tests."""
    with django_db_blocker.unblock():
        if not getattr(evennia, "_kotb_initialized", False):
            evennia._init()
            evennia._kotb_initialized = True
