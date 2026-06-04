"""Fixtures for world-build engine tests (requires pytest-django / Evennia).

The pure registry/spawner-helper tests (``test_templates.py`` and the pure cases
in ``test_spawner.py``) request no DB fixture; the spawner materialisation tests
mark ``@pytest.mark.django_db`` and rely on this session bootstrap, mirroring
``tests/zones/conftest.py`` and ``tests/engine/conftest.py``.
"""

from typing import Any

import evennia
import pytest


@pytest.fixture(scope="session", autouse=True)
def _bootstrap_evennia_world_build(django_db_setup: Any, django_db_blocker: Any) -> None:
    """Initialise the Evennia API once per session for world-build tests."""
    with django_db_blocker.unblock():
        # Other engine suites share this flag so _init runs at most once.
        if not getattr(evennia, "_kotb_initialized", False):
            evennia._init()
            evennia._kotb_initialized = True
