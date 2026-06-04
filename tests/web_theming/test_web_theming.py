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


def test_css_file_exists() -> None:
    assert CSS_PATH.exists(), f"Missing: {CSS_PATH}"


def test_css_variables() -> None:
    content = CSS_PATH.read_text()
    for var in CSS_VARIABLES:
        assert var in content, f"CSS variable {var!r} not found in theme.css"


def test_template_exists() -> None:
    assert TEMPLATE_PATH.exists(), f"Missing: {TEMPLATE_PATH}"


def test_template_extends() -> None:
    content = TEMPLATE_PATH.read_text()
    assert "extends" in content, "Template does not extend a base template"
    assert "extra_head" in content, "Template does not define an extra_head block"


def test_template_css_link() -> None:
    content = TEMPLATE_PATH.read_text()
    assert "theme.css" in content, "Template does not reference theme.css"


def test_connection_screen_title() -> None:
    content = SCREENS_PATH.read_text()
    assert "Keep on the Borderlands" in content, (
        "CONNECTION_SCREEN missing title 'Keep on the Borderlands'"
    )


def test_connection_screen_commands() -> None:
    content = SCREENS_PATH.read_text()
    assert "connect" in content, "CONNECTION_SCREEN missing 'connect'"
    assert "create" in content, "CONNECTION_SCREEN missing 'create'"
    assert "help" in content, "CONNECTION_SCREEN missing 'help'"
    assert "look" in content, "CONNECTION_SCREEN missing 'look'"


def test_servername_setting() -> None:
    content = SETTINGS_PATH.read_text()
    assert 'SERVERNAME = "Keep on the Borderlands"' in content, (
        'settings.py SERVERNAME is not "Keep on the Borderlands"'
    )
