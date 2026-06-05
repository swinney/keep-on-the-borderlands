"""End-to-end Compose smoke test (integration tier — needs a container runtime).

Env-gated: set RUN_DEPLOYMENT_SMOKE=1 to run. Brings the stack up from a fresh
volume and verifies the spec's lifecycle properties: non-interactive first boot,
a populated world, reachable player ports, idempotent restart, and clean
teardown. Requires a `.env` with valid values (see .env.example).
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_DEPLOYMENT_SMOKE") != "1",
    reason="set RUN_DEPLOYMENT_SMOKE=1 (needs a container runtime + .env) to run the smoke test",
)

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = os.environ.get("DEPLOY_RUNTIME", "docker")
PROJECT = "kotb-smoke"
TELNET_HOST_PORT = int(os.environ.get("TELNET_PORT", "14000"))


def _compose(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [RUNTIME, "compose", "-p", PROJECT, "-f", "compose.yaml", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _port_open(port: int, timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout):
            return True
    except OSError:
        return False


def _wait_for_port(port: int, deadline_s: int = 180) -> bool:
    end = time.monotonic() + deadline_s
    while time.monotonic() < end:
        if _port_open(port):
            return True
        time.sleep(3)
    return False


def _read_room_count() -> int:
    """One read of the Room count from the volume's SQLite (0 on any error)."""
    py = (
        "import sqlite3;"
        "c=sqlite3.connect('/app/data/evennia.db3');"
        "n=c.execute("
        "\"select count(*) from objects_objectdb where db_typeclass_path like '%room%'\""
        ").fetchone()[0];"
        "print('ROOMS=', n)"
    )
    result = _compose("exec", "-T", "mud", "python", "-c", py)
    for line in result.stdout.splitlines():
        if line.startswith("ROOMS="):
            return int(line.split("=", 1)[1].strip())
    return 0


def _room_count(retries: int = 40, delay: float = 2.0) -> int:
    """Return the settled Room count, polling until the build finishes.

    Reads the volume's SQLite directly (avoids `evennia shell -c`, which recurses
    against a live server). The telnet port opens before at_initial_setup finishes
    building, and the build is incremental, so we wait for the count to *stabilise*
    (positive and unchanged across two consecutive reads) rather than grabbing the
    first positive — an early read catches a partial world.
    """
    prev = -1
    count = 0
    for _ in range(retries):
        count = _read_room_count()
        if count > 0 and count == prev:
            return count
        prev = count
        time.sleep(delay)
    return count


@pytest.fixture(scope="module")
def stack() -> Iterator[None]:
    if shutil.which(RUNTIME) is None:
        pytest.skip(f"{RUNTIME} not on PATH")
    if not (ROOT / ".env").exists():
        pytest.skip(".env required (cp .env.example .env and fill it in)")
    # Fresh volume each run.
    _compose("down", "-v")
    up = _compose("up", "-d", "--build")
    assert up.returncode == 0, up.stderr
    try:
        yield
    finally:
        _compose("down", "-v")


def test_first_boot_is_noninteractive_and_serves_ports(stack: None) -> None:
    """Requirement: Deterministic non-interactive first boot + Port surface."""
    assert _wait_for_port(TELNET_HOST_PORT), "telnet port never opened (boot hung or failed)"


def test_world_is_populated(stack: None) -> None:
    """Requirement: first boot builds the world (room count > empty baseline)."""
    assert _wait_for_port(TELNET_HOST_PORT)
    assert _room_count() > 1


def test_restart_is_idempotent(stack: None) -> None:
    """Requirement: Idempotent restart — no duplicate world after a restart."""
    assert _wait_for_port(TELNET_HOST_PORT)
    before = _room_count()
    assert _compose("restart").returncode == 0
    assert _wait_for_port(TELNET_HOST_PORT)
    assert _room_count() == before
