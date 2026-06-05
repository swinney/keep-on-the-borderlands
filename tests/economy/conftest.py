"""Fixtures for economy engine tests (requires pytest-django / Evennia).

Pure-core tests (test_economy_rules.py) never carry @pytest.mark.django_db so
this bootstrap skips entirely when they run in isolation; only the engine
command tests trigger the Evennia boot.
"""

import evennia
import pytest


@pytest.fixture(scope="session", autouse=True)
def _bootstrap_evennia_economy(request: pytest.FixtureRequest) -> None:
    """Initialise the Evennia API once per session, only when DB tests are present."""
    if not any(item.get_closest_marker("django_db") is not None for item in request.session.items):
        return
    request.getfixturevalue("django_db_setup")
    django_db_blocker = request.getfixturevalue("django_db_blocker")
    with django_db_blocker.unblock():
        if not getattr(evennia, "_kotb_initialized", False):
            evennia._init()
            evennia._kotb_initialized = True
