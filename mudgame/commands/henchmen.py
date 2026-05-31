"""Henchman order commands (docs/specs/henchmen.md §5)."""

from __future__ import annotations

from typing import Any, ClassVar

from evennia.commands.command import Command

from world.rules.henchmen import (
    ORDER_ATTACK,
    ORDER_DISMISS,
    ORDER_GUARD,
    VALID_ORDERS,
)

_PARSE_SPLIT = 2   # split args into at most 3 parts (maxsplit=2)
_PARTS_WITH_ARG = 3  # parts list has all three slots when an arg is present


class CmdOrder(Command):  # type: ignore[misc]
    """Issue a standing order to one of your henchmen.

    Usage:
      order <henchman> follow
      order <henchman> attack <target>
      order <henchman> guard <who>
      order <henchman> wait
      order <henchman> retreat
      order <henchman> dismiss
    """

    key = "order"
    aliases: ClassVar[list[str]] = []
    help_category = "Henchmen"

    def parse(self) -> None:
        parts = self.args.strip().split(None, _PARSE_SPLIT)
        self.henchman_name: str = parts[0] if parts else ""
        self.order_word: str = parts[1].lower() if len(parts) > 1 else ""
        self.order_arg: str = parts[2] if len(parts) >= _PARTS_WITH_ARG else ""

    def _find_henchman(self, caller: Any) -> Any:
        """Return the named henchman in the caller's room, or None."""
        for obj in list(caller.location.contents if caller.location else []):
            if (
                getattr(obj, "IS_HENCHMAN", False)
                and obj.db.employer == caller
                and self.henchman_name.lower() in obj.key.lower()
            ):
                return obj
        return None

    def _apply_targeted_order(self, caller: Any, henchman: Any) -> None:
        """Handle 'attack' and 'guard' orders that take a target argument."""
        if self.order_word == ORDER_ATTACK:
            prompt = "Attack whom? Usage: order <henchman> attack <target>"
        else:
            prompt = "Guard whom? Usage: order <henchman> guard <who>"

        if not self.order_arg:
            caller.msg(prompt)
            return
        target = caller.search(self.order_arg, location=caller.location)
        if not target:
            return
        henchman.db.own_target = target
        henchman.db.order = self.order_word
        verb = "attack" if self.order_word == ORDER_ATTACK else "guard"
        caller.msg(f"You order {henchman.key} to {verb} {target.key}.")

    def func(self) -> None:
        caller = self.caller
        if not self.henchman_name or not self.order_word:
            caller.msg("Usage: order <henchman> <follow|attack|guard|wait|retreat|dismiss>")
            return

        if self.order_word not in VALID_ORDERS:
            caller.msg(
                f"Unknown order '{self.order_word}'. Valid: {', '.join(sorted(VALID_ORDERS))}"
            )
            return

        henchman = self._find_henchman(caller)
        if henchman is None:
            caller.msg(f"You have no henchman named '{self.henchman_name}' here.")
            return

        if self.order_word == ORDER_DISMISS:
            henchman.db.employer = None
            henchman.db.order = "follow"
            caller.msg(f"{henchman.key} is dismissed.")
            if henchman.location:
                henchman.location.msg_contents(
                    f"{henchman.key} is released from service.",
                    exclude=[caller],
                )
            return

        if self.order_word in (ORDER_ATTACK, ORDER_GUARD):
            self._apply_targeted_order(caller, henchman)
            return

        henchman.db.order = self.order_word
        henchman.db.own_target = None
        caller.msg(f"You order {henchman.key} to {self.order_word}.")
