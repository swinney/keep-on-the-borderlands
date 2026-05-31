"""Smoke test.

Exists so the CI pipeline (ruff · mypy · pytest) has something concrete to
exercise from day one. Delete or replace once real subsystem tests land
under tests/<system>/ per CLAUDE.md §3.
"""


def test_smoke() -> None:
    assert True
