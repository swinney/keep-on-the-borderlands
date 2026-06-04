"""Tests for M14 web-client theming + MOTD (docs/specs/web-theming.md).

All tests are pure-Python file-content checks; no Evennia boot required.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
CSS_PATH = REPO_ROOT / "mudgame/web/static/webclient/css/theme.css"
TEMPLATE_PATH = REPO_ROOT / "mudgame/web/templates/webclient/webclient.html"
SCREENS_PATH = REPO_ROOT / "mudgame/server/conf/connection_screens.py"
SETTINGS_PATH = REPO_ROOT / "mudgame/server/conf/settings.py"

CSS_VARIABLES = [
    "--bg-color",
    "--text-color",
    "--accent-color",
    "--link-color",
    "--input-bg",
    "--input-text",
    "--border-color",
    "--scrollbar-color",
]


def _read(path: Path) -> str:
    """Read ``path``, failing with a clear message if it is missing.

    Each content test reads through this rather than ``Path.read_text`` directly,
    so a missing file fails with "Missing: …" regardless of test execution order
    (pytest does not guarantee order, so it can't lean on ``test_*_exists``).
    """
    assert path.exists(), f"Missing: {path}"
    return path.read_text()


def test_css_file_exists() -> None:
    assert CSS_PATH.exists(), f"Missing: {CSS_PATH}"


def test_css_variables() -> None:
    content = _read(CSS_PATH)
    for var in CSS_VARIABLES:
        assert var in content, f"CSS variable {var!r} not found in theme.css"


def test_template_exists() -> None:
    assert TEMPLATE_PATH.exists(), f"Missing: {TEMPLATE_PATH}"


def test_template_extends() -> None:
    content = _read(TEMPLATE_PATH)
    # Assert the exact Django tags the spec requires, not loose substrings: the
    # template must extend Evennia's webclient base and (re)define extra_head.
    assert '{% extends "webclient/base.html" %}' in content, (
        'Template must extend "webclient/base.html"'
    )
    assert "{% block extra_head %}" in content, "Template must define the extra_head block"


def test_template_css_link() -> None:
    content = _read(TEMPLATE_PATH)
    # The theme stylesheet must be injected via the static tag.
    assert "{% static 'webclient/css/theme.css' %}" in content, (
        "Template does not load theme.css via the {% static %} tag"
    )


def test_connection_screen_title() -> None:
    content = _read(SCREENS_PATH)
    assert "Keep on the Borderlands" in content, (
        "CONNECTION_SCREEN missing title 'Keep on the Borderlands'"
    )


def test_connection_screen_commands() -> None:
    content = _read(SCREENS_PATH)
    assert "connect" in content, "CONNECTION_SCREEN missing 'connect'"
    assert "create" in content, "CONNECTION_SCREEN missing 'create'"
    assert "help" in content, "CONNECTION_SCREEN missing 'help'"
    assert "look" in content, "CONNECTION_SCREEN missing 'look'"


def test_servername_setting() -> None:
    content = _read(SETTINGS_PATH)
    assert 'SERVERNAME = "Keep on the Borderlands"' in content, (
        'settings.py SERVERNAME is not "Keep on the Borderlands"'
    )
