"""Verify the env-config seams actually take effect in Django settings.

Boots the *real* settings module (``server.conf.settings``) once in a subprocess
with the relevant env vars set and reads back the effective Django settings. Runs
wherever Evennia is installed (CI, host venv); skipped otherwise. A single boot
keeps the (slow) Evennia/Django setup off the critical CI path.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("evennia")

GAME_DIR = Path(__file__).resolve().parents[2] / "mudgame"


def test_env_config_takes_effect_in_settings() -> None:
    """Requirement: SECRET_KEY and EVENNIA_DATA_DIR are read from the environment."""
    sentinel = "env-injected-secret-key-sentinel-value"
    data_dir = "/tmp/kotb-test-data"

    env = dict(os.environ)
    env["DJANGO_SETTINGS_MODULE"] = "server.conf.settings"
    env["SECRET_KEY"] = sentinel
    env["EVENNIA_DATA_DIR"] = data_dir
    code = (
        "import django; django.setup();"
        "from django.conf import settings;"
        "print('SECRET=' + str(settings.SECRET_KEY));"
        "print('DB=' + str(settings.DATABASES['default']['NAME']))"
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

    values = {
        line.split("=", 1)[0]: line.split("=", 1)[1]
        for line in result.stdout.splitlines()
        if line.startswith(("SECRET=", "DB="))
    }
    # SECRET_KEY from the environment overrides secret_settings.py.
    assert values.get("SECRET") == sentinel
    # EVENNIA_DATA_DIR relocates the DB so the volume need not shadow code.
    assert values.get("DB") == f"{data_dir}/evennia.db3"
