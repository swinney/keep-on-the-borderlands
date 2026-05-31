"""Proves the M2 engine test harness boots.

This is the contract for the first M2 task ("wire pytest-django for engine
tests"): with ``DJANGO_SETTINGS_MODULE`` pointed at ``server.conf.test_settings``
and the engine bootstrap fixture in place, an engine test can load Django
settings, initialise the Evennia API, and round-trip an object through the ORM.
Later M2 tasks (typeclasses, the round loop, the ``attack`` command) build on
exactly this harness.
"""

import evennia
import pytest
from django.conf import settings
from evennia.utils import create


@pytest.mark.django_db
def test_test_environment_flag_is_set() -> None:
    """The test-settings shim enables Evennia's TEST_ENVIRONMENT branch."""
    assert settings.TEST_ENVIRONMENT is True


@pytest.mark.django_db
def test_evennia_api_initialised() -> None:
    """``evennia._init()`` has populated the lazy API handlers."""
    assert evennia.SESSION_HANDLER is not None


@pytest.mark.django_db
def test_orm_object_roundtrip() -> None:
    """A typeclassed object can be created and persisted to the test DB."""
    obj = create.create_object("typeclasses.objects.Object", key="harness-probe")
    try:
        assert obj.pk is not None
        assert obj.key == "harness-probe"
    finally:
        obj.delete()
