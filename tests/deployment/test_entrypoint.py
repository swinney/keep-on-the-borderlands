"""Control-flow unit tests for docker/entrypoint.sh (game-deployment spec).

These verify the boot *sequence* and *fail-fast validation* without Evennia or a
container, using the entrypoint's ENTRYPOINT_DRY_RUN hook. Real execution
correctness (migrate, idempotent superuser, build_all populating the world) is
covered by the env-gated smoke tier in test_smoke.py.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

ENTRYPOINT = Path(__file__).resolve().parents[2] / "docker" / "entrypoint.sh"
REQUIRED_VARS = ["SECRET_KEY", "DJANGO_SUPERUSER_USERNAME", "DJANGO_SUPERUSER_PASSWORD"]
_BASE_ENV = {"PATH": os.environ.get("PATH", "/usr/bin:/bin")}


def _run(extra_env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    """Run the entrypoint with a minimal env plus ``extra_env``."""
    env = {**_BASE_ENV, **extra_env}
    return subprocess.run(
        ["bash", str(ENTRYPOINT)],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _full_env() -> dict[str, str]:
    return {
        "SECRET_KEY": "x",
        "DJANGO_SUPERUSER_USERNAME": "admin",
        "DJANGO_SUPERUSER_PASSWORD": "pw",
    }


def test_entrypoint_has_bash_shebang() -> None:
    """The script is a bash script (executed as PID 1)."""
    first_line = ENTRYPOINT.read_text().splitlines()[0]
    assert first_line.startswith("#!")
    assert "bash" in first_line


def test_missing_all_required_env_fails_fast() -> None:
    """No config at all -> non-zero exit naming every missing variable."""
    result = _run({})
    assert result.returncode != 0
    for var in REQUIRED_VARS:
        assert var in result.stderr


@pytest.mark.parametrize("omit", REQUIRED_VARS)
def test_each_missing_required_var_is_named(omit: str) -> None:
    """Omitting any single required variable fails fast and names that variable."""
    env = _full_env()
    del env[omit]
    result = _run(env)
    assert result.returncode != 0
    assert omit in result.stderr


def test_dry_run_succeeds_with_full_config() -> None:
    """Full config + dry run validates and exits 0 without executing anything."""
    result = _run({**_full_env(), "ENTRYPOINT_DRY_RUN": "1"})
    assert result.returncode == 0


def test_dry_run_plan_is_ordered_and_complete() -> None:
    """The boot plan covers migrate, idempotent superuser, start, and build verify.

    Asserts the spec-required ordering: migrate, then the superuser (account #1,
    which at_initial_setup needs), then `evennia start` (whose at_initial_setup
    runs build_all()), then an explicit world-build verification.
    """
    result = _run({**_full_env(), "ENTRYPOINT_DRY_RUN": "1"})
    out = result.stdout

    assert "migrate" in out
    assert "superuser" in out
    assert "build_all()" in out  # named in the plan as what at_initial_setup runs
    assert "evennia start" in out
    assert "verify world built" in out

    assert out.index("migrate") < out.index("superuser")
    assert out.index("superuser") < out.index("evennia start")
    assert out.index("evennia start") < out.index("verify world built")
