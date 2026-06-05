"""Verify the env-config seams actually take effect in Django settings.

Boots the *real* settings module (``server.conf.settings``) in a subprocess with
the relevant env var set and reads back the effective Django setting. Runs
wherever Evennia is installed (CI, host venv); skipped otherwise.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("evennia")

GAME_DIR = Path(__file__).resolve().parents[2] / "mudgame"


def _effective(expr: str, extra_env: dict[str, str]) -> str:
    """Return ``str(expr)`` evaluated against booted Django settings, via subprocess."""
    env = dict(os.environ)
    env.update(extra_env)
    env["DJANGO_SETTINGS_MODULE"] = "server.conf.settings"
    code = (
        "import django; django.setup();"
        "from django.conf import settings;"
        f"print('RESULT=' + str({expr}))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=GAME_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    for line in result.stdout.splitlines():
        if line.startswith("RESULT="):
            return line[len("RESULT=") :]
    raise AssertionError(f"no RESULT line in output:\n{result.stdout}\n{result.stderr}")


def test_secret_key_comes_from_environment() -> None:
    """Requirement: SECRET_KEY comes from the environment (overrides secret_settings)."""
    sentinel = "env-injected-secret-key-sentinel-value"
    assert _effective("settings.SECRET_KEY", {"SECRET_KEY": sentinel}) == sentinel


def test_data_dir_relocates_the_database() -> None:
    """Requirement: EVENNIA_DATA_DIR relocates the DB so the volume need not shadow code."""
    data_dir = "/tmp/kotb-test-data"
    db_path = _effective("settings.DATABASES['default']['NAME']", {"EVENNIA_DATA_DIR": data_dir})
    assert db_path == f"{data_dir}/evennia.db3"
