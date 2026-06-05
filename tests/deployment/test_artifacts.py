"""Static assertions on the deployment artifacts (game-deployment spec).

Cheap, runtime-free checks that the image is lean, the port surface is correct,
the volume does not shadow code, and the config seams exist — the spec
requirements that are verifiable from the files themselves.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text()


def test_runtime_image_is_lean_and_independent() -> None:
    """Requirement: Lean runtime image — no agent/dev tooling, not FROM the loop image."""
    text = _read("Containerfile.runtime")
    assert "FROM python:3.12-slim" in text
    assert "kotb-ralph" not in text  # not built on the loop image
    # No build agent or test/lint tooling installed.
    assert "npm install" not in text
    assert "nodejs" not in text
    assert "anthropic" not in text.lower()
    assert "pip install -e ." in text  # game runtime deps only


def test_runtime_image_exposes_player_ports_only() -> None:
    """Requirement: Port surface — declares player ports, not the internal ones."""
    text = _read("Containerfile.runtime")
    assert "EXPOSE 4000 4001 4002" in text


def test_compose_single_service_and_volume() -> None:
    """Requirement: Single-service model + persistence on a named volume."""
    text = _read("compose.yaml")
    assert "services:" in text
    assert "mud:" in text
    # DB persisted on a named volume mounted at the dedicated data dir.
    assert "gamedata:/app/data" in text
    assert "volumes:" in text


def test_compose_publishes_player_ports_not_internal() -> None:
    """Requirement: Port surface — 4000/4001/4002 published, 4005/4006 not."""
    text = _read("compose.yaml")
    assert ":4000" in text
    assert ":4001" in text
    assert ":4002" in text
    # Internal ports must not be PUBLISHED (host:container mappings).
    assert ":4005" not in text
    assert ":4006" not in text


def test_compose_lifecycle_directives() -> None:
    """Requirement: Clean shutdown + healthcheck covering the first-boot build."""
    text = _read("compose.yaml")
    assert "restart: unless-stopped" in text
    assert "stop_grace_period" in text
    assert "healthcheck:" in text
    assert "start_period" in text


def test_dockerignore_excludes_host_secrets_and_db() -> None:
    """Requirement: SECRET_KEY not baked into image; host DB not shipped."""
    text = _read(".dockerignore")
    assert "secret_settings.py" in text
    assert "*.db3" in text


def test_settings_reads_secret_key_and_data_dir_from_env() -> None:
    """Requirement: Configuration via environment — SECRET_KEY + EVENNIA_DATA_DIR seams."""
    text = _read("mudgame/server/conf/settings.py")
    assert 'environ.get("SECRET_KEY")' in text
    assert "SECRET_KEY = _env_secret_key" in text
    assert 'environ.get("EVENNIA_DATA_DIR")' in text


def test_env_example_documents_required_vars() -> None:
    """Requirement: Operator config — the template names every required variable."""
    text = _read(".env.example")
    for var in ("SECRET_KEY", "DJANGO_SUPERUSER_USERNAME", "DJANGO_SUPERUSER_PASSWORD"):
        assert var in text
