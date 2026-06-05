"""Image-content assertions (integration tier — needs a container runtime).

Env-gated: set RUN_DEPLOYMENT_SMOKE=1 to run. Builds the runtime image and
verifies it is lean — Evennia present, build agent / node absent.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_DEPLOYMENT_SMOKE") != "1",
    reason="set RUN_DEPLOYMENT_SMOKE=1 (needs a container runtime) to run image tests",
)

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = os.environ.get("DEPLOY_RUNTIME", "docker")
IMAGE = "kotb-mud-imagetest"


def _runtime_available() -> bool:
    return shutil.which(RUNTIME) is not None


@pytest.fixture(scope="module")
def built_image() -> str:
    if not _runtime_available():
        pytest.skip(f"{RUNTIME} not on PATH")
    build = subprocess.run(
        [RUNTIME, "build", "-f", "Containerfile.runtime", "-t", IMAGE, "."],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert build.returncode == 0, build.stderr
    return IMAGE


def test_image_has_evennia_and_no_agent_tooling(built_image: str) -> None:
    """Requirement: Lean runtime image — evennia present; claude/node/npm absent."""
    check = (
        "command -v evennia >/dev/null "
        "&& ! command -v claude >/dev/null "
        "&& ! command -v node >/dev/null "
        "&& ! command -v npm >/dev/null"
    )
    result = subprocess.run(
        [RUNTIME, "run", "--rm", "--entrypoint", "sh", built_image, "-c", check],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        "image must contain evennia and exclude claude/node/npm; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
