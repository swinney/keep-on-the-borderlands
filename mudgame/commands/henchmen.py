"""Henchman commands: tavern roster, hiring (§1), and standing orders (§5).

docs/specs/henchmen.md. The recruit roster is static config
(``world.henchmen.config.ROSTER``); ``roster`` and ``hire`` are room-scoped to
the Keep's ``tavern`` (zones/keep.md), mirroring the room-scoped shop commands
in ``commands.economy``. The pure hire math (reaction roll bands, CHA cap,
seeded loyalty) lives in ``world.rules.henchmen``; these commands only roll
dice, validate scope and funds, and create/charge.
"""

from __future__ import annotations

import random
from typing import Any, ClassVar

from evennia.commands.command import Command
from evennia.objects.models import ObjectDB
from evennia.utils import create

from world.henchmen.config import ROSTER, RosterEntry
from world.rules import dice
from world.rules.abilities import ability_modifier
from world.rules.henchmen import (
    ORDER_ATTACK,
    ORDER_DISMISS,
    ORDER_GUARD,
    VALID_ORDERS,
    HireOutcome,
    attempt_hire,
)

_PARSE_SPLIT = 2  # split args into at most 3 parts (maxsplit=2)
_PARTS_WITH_ARG = 3  # parts list has all three slots when an arg is present

TAVERN_ROOM_KEY = "tavern"
HENCHMAN_TYPECLASS = "typeclasses.npcs.Henchman"


def _room_key(caller: Any) -> str:
    """Return the caller's room ``room_key`` ('' when roomless or untagged)."""
    location = caller.location
    if location is None:
        return ""
    return str(location.db.room_key or "")


def _party_size(caller: Any) -> int:
    """Count the henchmen currently employed by ``caller`` (retainer-cap input)."""
    return sum(
        1
        for record in ObjectDB.objects.filter(db_typeclass_path=HENCHMAN_TYPECLASS)
        if record.db.employer == caller
    )


def _find_recruit(name: str) -> RosterEntry | None:
    """Return the roster entry matching display name ``name`` (case-insensitive)."""
    needle = name.lower()
    for entry in ROSTER:
        if needle == entry.name.lower():
            return entry
    for entry in ROSTER:
        if needle in entry.name.lower():
            return entry
    return None


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


class CmdRoster(Command):  # type: ignore[misc]
    """List the recruits available for hire at the tavern.

    Usage:
      roster
    """

    key = "roster"
    aliases: ClassVar[list[str]] = ["recruits"]
    help_category = "Henchmen"

    def func(self) -> None:
        caller = self.caller
        if _room_key(caller) != TAVERN_ROOM_KEY:
            caller.msg("There is no hiring hall here; recruits gather at the tavern.")
            return
        lines = ["Recruits for hire (use 'hire <name>'):"]
        lines.extend(
            f"  {entry.name} - {entry.role} (level {entry.level}) - {entry.hire_fee} gp"
            for entry in ROSTER
        )
        caller.msg("\n".join(lines))


class CmdHire(Command):  # type: ignore[misc]
    """Hire a recruit from the tavern roster.

    Usage:
      hire <name>

    Resolves an OSE reaction roll (2d6 + your CHA modifier): a poor result and
    the recruit declines at no cost; a good result charges the hire fee and the
    henchman joins your party. Blocked if you are at your charisma retainer cap
    or cannot afford the fee.
    """

    key = "hire"
    aliases: ClassVar[list[str]] = []
    help_category = "Henchmen"

    def parse(self) -> None:
        self.recruit_name = self.args.strip()

    def func(self) -> None:
        caller = self.caller
        if _room_key(caller) != TAVERN_ROOM_KEY:
            caller.msg("There is no one here to hire.")
            return
        if not self.recruit_name:
            caller.msg("Hire whom? See 'roster' for available recruits.")
            return
        entry = _find_recruit(self.recruit_name)
        if entry is None:
            caller.msg(f"No recruit named '{self.recruit_name}' is on the roster.")
            return

        cha_score = int(caller.traits.cha.value)
        rng = random.Random()
        reaction = dice.roll("2d6", rng=rng) + ability_modifier(cha_score)
        result = attempt_hire(
            cha_score=cha_score,
            hire_fee=entry.hire_fee,
            current_party_size=_party_size(caller),
            reaction_roll_total=reaction,
        )

        if result.outcome is HireOutcome.CAP_REACHED:
            caller.msg("You already command as many retainers as your charisma allows.")
            return
        if result.outcome is HireOutcome.REFUSED:
            caller.msg(f"{entry.name} looks you over and declines.")
            return

        coin = int(caller.db.coin or 0)
        if coin < result.fee_paid:
            caller.msg(f"You can't afford {entry.name}'s fee of {entry.hire_fee} gp.")
            return

        caller.db.coin = coin - result.fee_paid
        henchman = create.create_object(
            HENCHMAN_TYPECLASS, key=entry.name, location=caller.location
        )
        henchman.db.employer = caller
        henchman.db.loyalty = result.initial_loyalty
        henchman.db.order = "follow"
        henchman.db.roster_key = entry.key
        caller.msg(
            f"{entry.name} agrees to follow you for {result.fee_paid} gp. "
            f"({coin - result.fee_paid} gp left.)"
        )
