"""Fixtures for the game-deployment tests (game-deployment spec / ADR-0006).

These tests are Django-free by construction: the unit tier exercises the
entrypoint shell script and asserts on the static deployment artifacts
(``compose.yaml``, ``Containerfile.runtime``, ``.dockerignore``, the settings
shim), so — unlike the engine suites — there is no Evennia bootstrap to guard.
``test_secret_key.py`` boots Django in a *subprocess* (never the test process),
and the image/smoke tiers shell out to a container runtime and are env-gated.
"""

from __future__ import annotations

from pathlib import Path

import pytest

# tests/deployment/conftest.py -> parents[2] == repo root.
REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Absolute path to the repository root."""
    return REPO_ROOT
