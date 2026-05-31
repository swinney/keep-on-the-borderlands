"""Persistent leaderboard for hardcore fell entries (specs/death.md §3)."""

from __future__ import annotations

from typing import Any, cast

from evennia.server.models import ServerConfig

_FELL_KEY = "leaderboard_fell"


def append_fell(entry: dict[str, Any]) -> None:
    """Append a hardcore death entry to the persistent fell leaderboard."""
    fell = get_fell_entries()
    fell.append(entry)
    ServerConfig.objects.conf(_FELL_KEY, value=fell)


def get_fell_entries() -> list[dict[str, Any]]:
    """Return all fell leaderboard entries."""
    result = ServerConfig.objects.conf(_FELL_KEY, default=None)
    if result is None:
        return []
    return cast(list[dict[str, Any]], list(result))
