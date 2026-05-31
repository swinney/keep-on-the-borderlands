"""Faction-related commands: consider.

docs/specs/faction.md §5 — surfaces player standing in flavor text.
"""

from __future__ import annotations

from typing import ClassVar

from evennia.commands.command import Command
from evennia.utils.search import search_script

_CONSIDER_MESSAGES: dict[str, str] = {
    "kill-on-sight": "{name} snarls — it would kill you on sight.",
    "hostile": "{name} glares at you with open hostility.",
    "neutral": "{name} regards you with indifference.",
    "friendly": "{name} regards you with warmth.",
}


class CmdConsider(Command):  # type: ignore[misc]
    """Gauge how a nearby creature regards you.

    Usage:
      consider <target>

    Surfaces your faction standing with the target in flavor text.
    """

    key = "consider"
    aliases: ClassVar[list[str]] = []
    help_category = "Faction"

    def parse(self) -> None:
        self.target_name = self.args.strip()

    def func(self) -> None:
        caller = self.caller
        if not self.target_name:
            caller.msg("Consider what?")
            return
        target = caller.search(self.target_name, location=caller.location)
        if not target:
            return
        faction_id: object = getattr(target, "db", None) and target.db.faction_id
        if not faction_id:
            caller.msg(f"{target.key} belongs to no faction.")
            return
        results = search_script("faction_manager")
        if not results:
            band = "neutral"
        else:
            band = str(results[0].standing_band(str(faction_id), str(caller.id)))
        template = _CONSIDER_MESSAGES.get(band, "{name} belongs to a faction.")
        caller.msg(template.format(name=target.key))
