"""Quest-giver commands — list, accept, and turn in quests at a giver NPC.

Room-scoped like the tavern/shop commands: ``quests``/``accept``/``turnin``
operate against whichever quest-giver ServiceNpc shares the caller's room (the
Guildmaster in the guildhall, the Castellan in his audience chamber, and so on),
resolved by ``_giver_here``. Each giver offers its slice of the catalog
(``world.quests.config.quests_from``); the pure state machine
(``world.quests.state``) derives availability and tracks kill progress, credited
by ``Mob.at_death`` (``typeclasses.npcs``).

Completion fires the quest's cross-system effects (quests.md §8): a coin/XP
reward, the R2 faction standing shift, and — for the two Castellan story quests —
the **season-global** events. ``c_expose_priest`` reports the disguised spy to
the Castellan with the player's gathered evidence, tripping the server-global
exposure (R4); ``c_destroy_shrine`` cleanses the Altar of Chaos, ending the
season early (R6). Both are delivered by their global-Script managers, so the
turn-in only reaches them when the manager is live.
"""

from __future__ import annotations

import time
from typing import Any, ClassVar

from evennia.commands.command import Command
from evennia.utils.search import search_script

from world.priest.evidence import Evidence
from world.quests import state as qstate
from world.quests.config import (
    GIVERS,
    SEASON_END_SEASON,
    SEASON_EXPOSE_PRIEST,
    Quest,
    quests_from,
)


def _giver_here(caller: Any) -> str | None:
    """The quest-giver key for a giver ServiceNpc in the caller's room, or None.

    Matches a service NPC whose ``role`` is a known catalog giver
    (``world.quests.config.GIVERS``) — the Guildmaster, Castellan, Curate, etc.
    Tribe chiefs are plain ``Mob``s in the caves, not service NPCs, so they are
    never resolved here.
    """
    location = caller.location
    if location is None:
        return None
    for obj in location.contents:
        if getattr(obj, "IS_SERVICE_NPC", False) and str(obj.db.role or "") in GIVERS:
            return str(obj.db.role)
    return None


def _quest_log(caller: Any) -> qstate.QuestLog:
    """A mutable copy of the caller's quest log (empty when unset)."""
    return dict(caller.db.quests or {})


def _level(caller: Any) -> int:
    """The caller's character level (prereq input)."""
    return int(caller.traits.level.value)


def _player_evidence(caller: Any) -> Evidence:
    """Rebuild the caller's per-character priest evidence (R4 §3).

    Detection paths persist what a player has gathered under
    ``caller.db.priest_evidence`` as ``{"clue_sightings": [...],
    "strong_proofs": [...]}``; an unset attribute reads as no evidence.
    """
    raw = caller.db.priest_evidence or {}
    return Evidence(
        clue_sightings=raw.get("clue_sightings", ()),
        strong_proofs=raw.get("strong_proofs", ()),
    )


def _has_evidence(caller: Any) -> bool:
    """Whether the caller holds enough evidence to expose the spy (R4 §3)."""
    return _player_evidence(caller).can_report


def _match_offered(arg: str, giver: str) -> Quest | None:
    """Resolve one of ``giver``'s quests from a command argument (id or title)."""
    needle = arg.strip().lower()
    if not needle:
        return None
    for quest in quests_from(giver):
        if needle == quest.id.lower() or needle in quest.title.lower():
            return quest
    return None


class CmdQuests(Command):  # type: ignore[misc]
    """Read the quests a giver here is offering.

    Usage:
      quests

    Lists each quest the giver in this room offers and your progress on it. Use
    'accept <quest>' to take one and 'turnin <quest>' to claim its reward once it
    is done.
    """

    key = "quests"
    aliases: ClassVar[list[str]] = ["bounties"]
    help_category = "Quests"

    def func(self) -> None:
        caller = self.caller
        giver = _giver_here(caller)
        if giver is None:
            caller.msg("There is no one here offering quests.")
            return
        log = _quest_log(caller)
        level = _level(caller)
        has_evidence = _has_evidence(caller)
        now = time.time()
        lines = ["Quests offered here:"]
        for quest in quests_from(giver):
            entry = log.get(quest.id)
            state = qstate.status(
                quest, entry, level=level, now=now, log=log, has_evidence=has_evidence
            )
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
    """Accept a quest from the giver in this room.

    Usage:
      accept <quest>
    """

    key = "accept"
    aliases: ClassVar[list[str]] = []
    help_category = "Quests"

    def parse(self) -> None:
        self.target = self.args.strip()

    def func(self) -> None:
        caller = self.caller
        giver = _giver_here(caller)
        if giver is None:
            caller.msg("There is no one here to take a quest from.")
            return
        if not self.target:
            caller.msg("Accept which quest? See 'quests' for what is offered here.")
            return
        quest = _match_offered(self.target, giver)
        if quest is None:
            caller.msg(f"No quest called '{self.target}' is offered here.")
            return
        log = _quest_log(caller)
        entry = log.get(quest.id)
        level = _level(caller)
        has_evidence = _has_evidence(caller)
        now = time.time()
        if not qstate.can_accept(
            quest, entry, level=level, now=now, log=log, has_evidence=has_evidence
        ):
            state = qstate.status(
                quest, entry, level=level, now=now, log=log, has_evidence=has_evidence
            )
            if state == qstate.ACTIVE:
                caller.msg(f"You have already taken '{quest.title}'.")
            elif state == qstate.COMPLETE:
                caller.msg(f"You have done '{quest.title}'; it is not offered again yet.")
            else:
                caller.msg(f"You are not yet eligible for '{quest.title}'.")
            return
        log[quest.id] = qstate.accept(quest, entry)
        caller.db.quests = log
        kills = qstate.kill_steps(quest)
        if kills:
            step = kills[0]
            caller.msg(f"You take '{quest.title}': slay {step.count} {step.faction}.")
        else:
            caller.msg(f"You take '{quest.title}'.")


class CmdTurnin(Command):  # type: ignore[misc]
    """Turn in a completed quest to the giver in this room for its reward.

    Usage:
      turnin <quest>
    """

    key = "turnin"
    aliases: ClassVar[list[str]] = ["turn-in"]
    help_category = "Quests"

    def parse(self) -> None:
        self.target = self.args.strip()

    def _fire_season_global(self, caller: Any, quest: Quest) -> bool:
        """Fire ``quest``'s season-global effect; return whether it succeeded.

        ``SEASON_EXPOSE_PRIEST`` reports the spy with the caller's evidence and
        succeeds only on the report that trips the server-global exposure (R4);
        a rejected report (too little evidence, no spy, or already exposed)
        returns False so the turn-in is held back. ``SEASON_END_SEASON`` ends the
        season early (R6) and always succeeds. A quest with no season-global tag,
        or one whose manager is not live, succeeds vacuously.
        """
        if quest.season_global == SEASON_EXPOSE_PRIEST:
            managers = search_script("priest_manager")
            if not managers:
                return False
            return bool(managers[0].report(_player_evidence(caller)))
        if quest.season_global == SEASON_END_SEASON:
            managers = search_script("season_manager")
            if managers:
                managers[0].end_season(reason="shrine_destroyed")
        return True

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
        giver = _giver_here(caller)
        if giver is None:
            caller.msg("There is no one here to claim a quest from.")
            return
        if not self.target:
            caller.msg("Turn in which quest? See 'quests' for what is offered here.")
            return
        quest = _match_offered(self.target, giver)
        if quest is None:
            caller.msg(f"No quest called '{self.target}' is offered here.")
            return
        log = _quest_log(caller)
        entry = log.get(quest.id)
        if entry is None or entry["state"] != qstate.ACTIVE:
            caller.msg(f"You have not taken '{quest.title}'.")
            return
        if not qstate.steps_met(quest, entry["progress"]):
            owed = qstate.remaining(quest, entry["progress"])
            detail = ", ".join(f"{count} {faction}" for faction, count in owed.items())
            caller.msg(f"'{quest.title}' is not finished — still owed: {detail}.")
            return
        if not self._fire_season_global(caller, quest):
            caller.msg(f"'{quest.title}' cannot be completed yet — suspicions, not proof.")
            return
        self._apply_reward(caller, quest)
        log[quest.id] = qstate.turn_in(quest, entry, now=time.time())
        caller.db.quests = log
        if quest.reward.gp:
            caller.msg(
                f"You complete '{quest.title}' and are paid {quest.reward.gp} gp. "
                "Bank your coin in the Keep to earn its experience."
            )
        else:
            caller.msg(f"You complete '{quest.title}'.")
