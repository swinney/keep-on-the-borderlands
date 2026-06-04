"""Quest-giver commands — list, accept, and turn in quests at a giver NPC.

Room-scoped like the tavern/shop commands: ``quests``/``accept``/``turnin``
operate against whichever quest-giver ServiceNpc shares the caller's room (the
Guildmaster in the guildhall, the Castellan in his audience chamber, and so on),
resolved by ``_giver_here``. Each giver offers its slice of the catalog
(``world.quests.config.quests_from``); the pure state machine
(``world.quests.state``) derives availability and tracks kill progress, credited
by ``Mob.at_death`` (``typeclasses.npcs``).

A deed-only quest (no kill steps) cannot be accepted and instantly turned in:
``turnin`` refuses until a world event has set the entry's deed-completion flag
(``world.quests.state.record_deed``). The exception is a quest whose deed *is*
the turn-in interaction — ``c_expose_priest`` (reporting the spy), gated by its
evidence requirement instead.

Completion fires the quest's cross-system effects (quests.md §8): a coin/XP
reward, the R2 faction standing shift, and the one season-global turn-in event.
``c_expose_priest`` reports the disguised spy to the Castellan with the player's
gathered evidence, tripping the server-global exposure (R4) — delivered by the
priest_manager, so the turn-in only reaches it when the manager is live.
``c_destroy_shrine`` grants only its reward here, gated on the shrine-destroyed
deed flag; the season-ending ``end_season`` is fired by the canonical
``Altar.at_destruction`` hook (typeclasses.objects), not the quest (review F4).
"""

from __future__ import annotations

import time
from typing import Any, ClassVar

from evennia.commands.command import Command
from evennia.utils import logger
from evennia.utils.search import search_script

from world.priest.config import CULT_FACTION_ID
from world.priest.evidence import Evidence
from world.priest.quests import SpyQuestLog, complete_spy_quest
from world.quests import state as qstate
from world.quests.config import (
    EVIDENCE_CURATE,
    GIVERS,
    SEASON_EXPOSE_PRIEST,
    Quest,
    quests_from,
)
from world.rules.combat import is_dead


def _giver_here(caller: Any) -> str | None:
    """The quest-giver key for a live giver NPC/mob in the caller's room, or None.

    Resolves on an explicit ``db.giver_key`` (world-build §8, M13 F1) — a stable
    key from ``world.quests.config.GIVERS`` set on every giver by the builder
    (Guildmaster, Castellan, Curate, Hermit, …) or the spawner (a quest-giving
    tribe chief). This is distinct from the display ``role``, so a giver whose
    role is a descriptor (the Hermit, the spy's chapel role) is still reachable.

    A tribe chief is both a kill target and a giver, so the giver must be **alive
    and present**: a dead chief (killed, or its corpse lingering before respawn)
    is skipped, and its quests are simply unavailable until it respawns (§8).
    """
    location = caller.location
    if location is None:
        return None
    for obj in location.contents:
        giver_key = obj.db.giver_key
        if not giver_key or str(giver_key) not in GIVERS:
            continue
        if _giver_dead(obj):
            continue
        return str(giver_key)
    return None


def _giver_dead(giver: Any) -> bool:
    """Whether a giver NPC/mob is dead (0 HP), so unavailable as a giver (§8).

    A static service NPC keeps its default 1-HP trait and never dies in the
    no-combat Keep, so this only excludes a slain tribe chief whose corpse still
    stands in its lair before the repop respawn. A giver with no HP trait is
    treated as alive (defensive).
    """
    traits = getattr(giver, "traits", None)
    hp = getattr(traits, "hp", None) if traits is not None else None
    if hp is None:
        return False
    return is_dead(int(hp.value))


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


def _meets_evidence(caller: Any, quest: Quest) -> bool:
    """Whether the caller clears ``quest``'s per-quest evidence gate (R4 §3).

    Evaluates the quest's ``evidence_min`` grade against the caller's gathered
    evidence: ``EVIDENCE_CURATE`` opens at the Curate's lower clue threshold,
    every other grade (``EVIDENCE_REPORT``) demands report-grade proof. A quest
    with no evidence gate (``evidence_min is None``) clears vacuously.
    """
    if quest.evidence_min is None:
        return True
    evidence = _player_evidence(caller)
    if quest.evidence_min == EVIDENCE_CURATE:
        return evidence.meets_curate_threshold
    return evidence.can_report


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
        now = time.time()
        lines = ["Quests offered here:"]
        for quest in quests_from(giver):
            entry = log.get(quest.id)
            state = qstate.status(
                quest,
                entry,
                level=level,
                now=now,
                log=log,
                has_evidence=_meets_evidence(caller, quest),
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
        has_evidence = _meets_evidence(caller, quest)
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
        """Fire ``quest``'s evidence-gated season-global effect; return success.

        Only ``SEASON_EXPOSE_PRIEST`` acts at turn-in: it reports the spy with the
        caller's evidence and succeeds only on the report that trips the
        server-global exposure (R4); a rejected report (too little evidence, no spy,
        or already exposed) returns False so the turn-in is held back.
        ``c_destroy_shrine``'s ``end_season`` is *not* fired here — the canonical R6
        trigger is the ``Altar.at_destruction`` hook (review F4), so its turn-in only
        grants the reward (gated on the shrine-destroyed deed flag). Any other quest
        succeeds vacuously.
        """
        if quest.season_global == SEASON_EXPOSE_PRIEST:
            managers = search_script("priest_manager")
            if not managers:
                return False
            return bool(managers[0].report(_player_evidence(caller)))
        return True

    def _apply_reward(self, caller: Any, quest: Quest) -> None:
        """Pay the gp/xp/item reward and fire the quest's faction effects (R2).

        Coin and XP go straight onto the character; ``quest.reward.items`` (holy
        water, the Shrine map, the relic — quests.md §9.3) are appended to the
        caller's ``quest_items`` inventory list so an item-reward quest actually
        delivers its items on turn-in.
        """
        if quest.reward.gp:
            caller.db.coin = int(caller.db.coin or 0) + quest.reward.gp
        if quest.reward.xp:
            caller.traits.xp.current = int(caller.traits.xp.current) + quest.reward.xp
        if quest.reward.items:
            items = list(caller.db.quest_items or [])
            items.extend(quest.reward.items)
            caller.db.quest_items = items
        self._apply_faction_effects(caller, quest)

    def _apply_faction_effects(self, caller: Any, quest: Quest) -> None:
        """Fire a completed quest's faction standing and relation effects (R2).

        ``harm_faction``/``aid_faction`` shift the player's standing with a
        faction (quests.md §8.4); ``tension_pair`` escalates a rivalry toward war
        (§8.5); ``breaks_alliance`` dissolves a pair's alliance (§8.6, the
        bribe-the-ogre quest). No-op when the faction_manager is not live.
        """
        managers = search_script("faction_manager")
        if not managers:
            return
        fm = managers[0]
        player_key = str(caller.id)
        if quest.harm_faction:
            fm.apply_quest_harm(quest.harm_faction, player_key)
        if quest.aid_faction:
            fm.apply_quest_aid(quest.aid_faction, player_key)
        if quest.tension_pair:
            fm.apply_quest_aid_vs(*quest.tension_pair)
        if quest.breaks_alliance:
            fm.apply_break_alliance(*quest.breaks_alliance)

    def _advance_cult_chain(self, caller: Any, quest: Quest) -> None:
        """Advance the disguised-priest cult chain on turn-in of an aids_cult quest.

        Records the completion on the caller's per-character spy-quest log
        (``caller.db.spy_quests``); on the completion that first reaches
        ``SPY_QUESTS_TO_AMBUSH`` the Caves ambush springs *once* — the player is
        branded a cult collaborator (cult standing rises, R2) and the ambush is
        logged. Live ambush-mob spawning rides the project-wide stubbed spawner;
        the observable effects (the standing gain, the brand) fire here. (R4 §4)
        """
        if not quest.aids_cult:
            return
        log = SpyQuestLog(caller.db.spy_quests or ())
        sprung = complete_spy_quest(log, quest.id)
        caller.db.spy_quests = sorted(log.completed)
        if not sprung:
            return
        managers = search_script("faction_manager")
        if managers:
            managers[0].apply_quest_aid(CULT_FACTION_ID, str(caller.id))
        logger.log_info(
            f"quests: {caller} sprang the cult Caves ambush "
            f"(reached {len(log.completed)} spy quests; last={quest.id})."
        )
        caller.msg("Too late, you sense the trap — cultists erupt from the Caves in ambush!")

    def _resolve_target(self, caller: Any) -> Quest | None:
        """The quest the caller named for turn-in, or None after messaging why not."""
        giver = _giver_here(caller)
        if giver is None:
            caller.msg("There is no one here to claim a quest from.")
            return None
        if not self.target:
            caller.msg("Turn in which quest? See 'quests' for what is offered here.")
            return None
        quest = _match_offered(self.target, giver)
        if quest is None:
            caller.msg(f"No quest called '{self.target}' is offered here.")
            return None
        return quest

    def func(self) -> None:
        caller = self.caller
        quest = self._resolve_target(caller)
        if quest is None:
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
        if qstate.requires_deed_flag(quest) and not qstate.deed_satisfied(entry):
            caller.msg(f"'{quest.title}' is not done — the deed itself remains unfulfilled.")
            return
        if not self._fire_season_global(caller, quest):
            caller.msg(f"'{quest.title}' cannot be completed yet — suspicions, not proof.")
            return
        self._apply_reward(caller, quest)
        self._advance_cult_chain(caller, quest)
        log[quest.id] = qstate.turn_in(quest, entry, now=time.time())
        caller.db.quests = log
        if quest.reward.gp:
            caller.msg(
                f"You complete '{quest.title}' and are paid {quest.reward.gp} gp. "
                "Bank your coin in the Keep to earn its experience."
            )
        else:
            caller.msg(f"You complete '{quest.title}'.")
