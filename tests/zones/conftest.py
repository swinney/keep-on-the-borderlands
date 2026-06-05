"""Fixtures for zone engine tests (requires pytest-django / Evennia).

Pure-data zone tests (e.g. test_keep.py) never carry @pytest.mark.django_db so
this bootstrap skips entirely when they run in isolation; the engine
(@pytest.mark.django_db) tests in this directory — the build-time and
populated-world suites (test_keep_build.py, test_caves.py, test_shrine_build.py,
…) — trigger the Evennia boot once per session.
"""

import evennia
import pytest


@pytest.fixture(scope="session", autouse=True)
def _bootstrap_evennia_zones(request: pytest.FixtureRequest) -> None:
    """Initialise the Evennia API once per session, only when DB tests are present."""
    if not any(item.get_closest_marker("django_db") is not None for item in request.session.items):
        return
    request.getfixturevalue("django_db_setup")
    django_db_blocker = request.getfixturevalue("django_db_blocker")
    with django_db_blocker.unblock():
        # Other engine suites share this flag so _init runs at most once.
        if not getattr(evennia, "_kotb_initialized", False):
            evennia._init()
            evennia._kotb_initialized = True
