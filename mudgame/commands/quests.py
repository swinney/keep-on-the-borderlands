"""Guildmaster quest commands — M9 tribe-clearing bounty slice (docs/specs/quests.md §2).

Room-scoped to the Keep's ``guild`` room (mirroring the tavern-scoped
roster/hire commands in ``commands.henchmen``), these wire the one M9 bounty —
"Cull the Kobolds" — end to end: ``quests`` lists it, ``accept`` takes it, and
``turnin`` pays out once the kill steps are met. Kill progress is credited by
``Mob.at_death`` (``typeclasses.npcs``); the pure state machine lives in
``world.quests.state`` and the catalog/tuning in ``world.quests.config``.

The bounty pays its reward as coin; that coin becomes XP when the player secures
it in the Keep or banks it (economy.md §6) — the M9 "treasure→XP-on-secure loop".
"""

from __future__ import annotations

import time
from typing import Any, ClassVar

from evennia.commands.command import Command
from evennia.utils.search import search_script

from world.quests import state as qstate
from world.quests.config import GUILDMASTER, Quest, quests_from

GUILD_ROOM_KEY = "guild"


def _room_key(caller: Any) -> str:
    """Return the caller's room ``room_key`` ('' when roomless or untagged)."""
    location = caller.location
    if location is None:
        return ""
    return str(location.db.room_key or "")


def _at_guildmaster(caller: Any) -> bool:
    """True when the caller stands in the Guildhall (where bounties are handled)."""
    return _room_key(caller) == GUILD_ROOM_KEY


def _quest_log(caller: Any) -> qstate.QuestLog:
    """A mutable copy of the caller's quest log (empty when unset)."""
    return dict(caller.db.quests or {})


def _level(caller: Any) -> int:
    """The caller's character level (prereq input)."""
    return int(caller.traits.level.value)


def _match_offered(arg: str) -> Quest | None:
    """Resolve a Guildmaster quest from a command argument (id or title text)."""
    needle = arg.strip().lower()
    if not needle:
        return None
    for quest in quests_from(GUILDMASTER):
        if needle == quest.id.lower() or needle in quest.title.lower():
            return quest
    return None


class CmdQuests(Command):  # type: ignore[misc]
    """Read the Guildmaster's bounty board.

    Usage:
      quests

    Lists each standing bounty and your progress on it. Use 'accept <bounty>'
    to take one and 'turnin <bounty>' to claim its reward once it is done.
    """

    key = "quests"
    aliases: ClassVar[list[str]] = ["bounties"]
    help_category = "Quests"

    def func(self) -> None:
        caller = self.caller
        if not _at_guildmaster(caller):
            caller.msg("There is no bounty board here; the Guildmaster keeps one at the guildhall.")
            return
        log = _quest_log(caller)
        level = _level(caller)
        now = time.time()
        lines = ["The Guildmaster's bounty board:"]
        for quest in quests_from(GUILDMASTER):
            entry = log.get(quest.id)
            state = qstate.status(quest, entry, level=level, now=now, log=log)
            lines.append(f"  {quest.title} [{quest.id}] - {state}")
            if state == qstate.ACTIVE and entry is not None:
                owed = qstate.remaining(quest, entry["progress"])
                detail = ", ".join(f"{count} {faction}" for faction, count in owed.items())
                done = qstate.steps_met(quest, entry["progress"])
                lines.append(f"    remaining: {detail if not done else 'none — ready to turn in'}")
            elif state == qstate.AVAILABLE:
                kills = qstate.kill_steps(quest)
                if kills:
                    step = kills[0]
                    lines.append(
                        f"    objective: slay {step.count} {step.faction}"
                        f" - reward {quest.reward.gp} gp"
                    )
        caller.msg("\n".join(lines))


class CmdAccept(Command):  # type: ignore[misc]
    """Accept one of the Guildmaster's bounties.

    Usage:
      accept <bounty>
    """

    key = "accept"
    aliases: ClassVar[list[str]] = []
    help_category = "Quests"

    def parse(self) -> None:
        self.target = self.args.strip()

    def func(self) -> None:
        caller = self.caller
        if not _at_guildmaster(caller):
            caller.msg("There is no one here to take a bounty from.")
            return
        if not self.target:
            caller.msg("Accept which bounty? See 'quests' for the board.")
            return
        quest = _match_offered(self.target)
        if quest is None:
            caller.msg(f"The Guildmaster offers no bounty called '{self.target}'.")
            return
        log = _quest_log(caller)
        entry = log.get(quest.id)
        now = time.time()
        if not qstate.can_accept(quest, entry, level=_level(caller), now=now, log=log):
            state = qstate.status(quest, entry, level=_level(caller), now=now, log=log)
            if state == qstate.ACTIVE:
                caller.msg(f"You have already taken '{quest.title}'.")
            elif state == qstate.COMPLETE:
                caller.msg(f"You have done '{quest.title}'; it is not yet posted again.")
            else:
                caller.msg(f"You are not yet seasoned enough for '{quest.title}'.")
            return
        log[quest.id] = qstate.accept(quest, entry)
        caller.db.quests = log
        kills = qstate.kill_steps(quest)
        if kills:
            step = kills[0]
            caller.msg(f"You take the bounty '{quest.title}': slay {step.count} {step.faction}.")
        else:
            caller.msg(f"You take the bounty '{quest.title}'.")


class CmdTurnin(Command):  # type: ignore[misc]
    """Turn in a completed bounty to the Guildmaster for its reward.

    Usage:
      turnin <bounty>
    """

    key = "turnin"
    aliases: ClassVar[list[str]] = ["turn-in"]
    help_category = "Quests"

    def parse(self) -> None:
        self.target = self.args.strip()

    def _apply_reward(self, caller: Any, quest: Quest) -> None:
        """Pay the gp/xp reward and apply the completion standing shift (R2)."""
        if quest.reward.gp:
            caller.db.coin = int(caller.db.coin or 0) + quest.reward.gp
        if quest.reward.xp:
            caller.traits.xp.current = int(caller.traits.xp.current) + quest.reward.xp
        if quest.harm_faction:
            managers = search_script("faction_manager")
            if managers:
                managers[0].apply_quest_harm(quest.harm_faction, str(caller.id))

    def func(self) -> None:
        caller = self.caller
        if not _at_guildmaster(caller):
            caller.msg("There is no one here to claim a bounty from.")
            return
        if not self.target:
            caller.msg("Turn in which bounty? See 'quests' for the board.")
            return
        quest = _match_offered(self.target)
        if quest is None:
            caller.msg(f"The Guildmaster offers no bounty called '{self.target}'.")
            return
        log = _quest_log(caller)
        entry = log.get(quest.id)
        if entry is None or entry["state"] != qstate.ACTIVE:
            caller.msg(f"You have not taken the bounty '{quest.title}'.")
            return
        if not qstate.steps_met(quest, entry["progress"]):
            owed = qstate.remaining(quest, entry["progress"])
            detail = ", ".join(f"{count} {faction}" for faction, count in owed.items())
            caller.msg(f"'{quest.title}' is not finished — still owed: {detail}.")
            return
        self._apply_reward(caller, quest)
        log[quest.id] = qstate.turn_in(quest, entry, now=time.time())
        caller.db.quests = log
        caller.msg(
            f"The Guildmaster pays you {quest.reward.gp} gp for '{quest.title}'. "
            "Bank your coin in the Keep to earn its experience."
        )
