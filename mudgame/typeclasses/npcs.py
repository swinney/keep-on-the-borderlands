"""Mob typeclass for monsters and NPCs with OSE stats wired via the traits contrib."""

from __future__ import annotations

from evennia.contrib.rpg.traits import TraitHandler
from evennia.objects.objects import DefaultCharacter
from evennia.utils import create, lazy_property
from evennia.utils.search import search_script

from world.quests import state as quest_state
from world.quests.config import CATALOG as QUEST_CATALOG
from world.rules.abilities import ability_modifier
from world.rules.combat import armor_class, is_dead

from .objects import ObjectParent


class Mob(ObjectParent, DefaultCharacter):
    """Base NPC/monster typeclass. Not player-puppeted under normal operation."""

    IS_MOB: bool = True

    @lazy_property
    def traits(self) -> TraitHandler:
        return TraitHandler(self)

    def at_object_creation(self) -> None:
        super().at_object_creation()
        t = self.traits
        for key, name in (
            ("str", "Strength"),
            ("int", "Intelligence"),
            ("wis", "Wisdom"),
            ("dex", "Dexterity"),
            ("con", "Constitution"),
            ("cha", "Charisma"),
        ):
            t.add(key, name, trait_type="static", base=10, mod=0)
        t.add("hp", "Hit Points", trait_type="gauge", base=1, mod=0)
        t.add("ac", "Armor Class", trait_type="static", base=10, mod=0)
        t.add("attack_bonus", "Attack Bonus", trait_type="static", base=0, mod=0)
        t.add("level", "Level", trait_type="static", base=1, mod=0)
        t.add("xp", "Experience Points", trait_type="counter", base=0, min=0, max=None)
        t.add("morale", "Morale", trait_type="static", base=7, mod=0)
        self.db.char_class = None
        self.db.faction_id = None
        # True for chief/shaman spawns: their death credits the killer the larger
        # kill_leader standing hit instead of kill_member (faction.md §2.1).
        self.db.is_leader = False
        # The character whose blow this mob last took; CmdAttack records it so a
        # faction mob's death can credit the right player's standing (§2.1).
        self.db.last_attacker = None
        # Set when this mob is a repop spawn-point instance (repop.md §1); its
        # death is reported to the repop_manager so the tribe respawns and the
        # leadership halt + rival scouting can fire (repop.md §3-4).
        self.db.spawn_id = None
        # Set when this mob is a rival scouting-party instance (repop.md §4); its
        # death reports via notify_scout_death instead of the respawn path — a
        # killed scout does not respawn, and credit goes to its rival faction.
        self.db.scout_id = None
        # Set on a chief/NPC who also gives quests (world-build §8, M13 F1); a
        # giver-key from world.quests.config.GIVERS. None for the rank-and-file.
        self.db.giver_key = None

    @property
    def computed_ac(self) -> int:
        dex_score: int = int(self.traits.dex.value)  # type: ignore[union-attr]
        # Single source of truth for the AC formula (matches PlayerCharacter).
        return armor_class(dex_modifier=ability_modifier(dex_score))

    def at_death(self) -> None:
        """Death handoff stub — M3/M5 expand this to XP award + loot (combat.md §4.2).

        A faction mob spawned by the repop manager carries a ``spawn_id``;
        reporting its death lets the manager schedule the respawn and fire the
        leadership halt + rival scouting once a tribe's chief and shaman are both
        down within one window (repop.md §3-4).
        """
        if self.location:
            self.location.msg_contents(f"{self.key} has been slain!", exclude=[])
        self._credit_faction_kill()
        self._credit_quest_kill()
        self._report_death_to_repop()

    def _credit_faction_kill(self) -> None:
        """Shift the slayer's standing with this mob's faction (faction.md §2.1).

        This is the M4↔M9 tie: killing kobolds drives the killer's kobold
        standing down (kill_member -3, or kill_leader -8 for a chief/shaman), so
        the inherited ``aggro_check`` then sees ``hostile``/``kill-on-sight`` and
        the surviving tribe turns on the player (faction.md §5). No-op for a mob
        with no faction or no recorded attacker (e.g. a death from other causes).
        """
        faction_id: object = self.db.faction_id
        if not faction_id:
            return
        player = self._responsible_player()
        player_key = str(getattr(player, "id", "") or "")
        if not player_key:
            return
        results = search_script("faction_manager")
        if not results:
            return
        mgr = results[0]
        if self.db.is_leader:
            mgr.apply_kill_leader(str(faction_id), player_key)
        else:
            mgr.apply_kill_member(str(faction_id), player_key)

    def _responsible_player(self) -> object | None:
        """The character who earns kill credit for this mob's death.

        Normally the recorded ``last_attacker``; when that attacker is a hired
        henchman the credit passes to its employer, so a player clearing a tribe
        through henchmen still earns the standing shift (henchmen.md §4).
        """
        attacker: object = self.db.last_attacker
        if attacker is not None and getattr(attacker, "IS_HENCHMAN", False):
            return attacker.db.employer
        return attacker

    def _credit_quest_kill(self) -> None:
        """Advance the killer's active tribe-clearing bounties (quests.md §2).

        Uses the same responsible-player resolution as the faction credit, so a
        kill landed by a hired henchman counts toward its employer's bounty
        (henchmen.md §4). No-op for a factionless mob, an unattributed death, or
        a non-player killer (another mob/henchman).
        """
        faction_id: object = self.db.faction_id
        if not faction_id:
            return
        player = self._responsible_player()
        if player is None or getattr(player, "IS_MOB", False):
            return
        log = dict(player.db.quests or {})
        if quest_state.record_faction_kill(log, QUEST_CATALOG, str(faction_id)):
            player.db.quests = log

    def _report_death_to_repop(self) -> None:
        """Notify the repop_manager of this mob's death (spawn point or rival scout).

        A spawn-point instance (``spawn_id``) schedules a respawn and may fire the
        leadership halt (repop.md §3). A rival-scout instance (``scout_id``) instead
        notifies ``notify_scout_death`` — the scout does not respawn, and the kill
        credits its rival faction's standing for the responsible player (repop.md §4).
        """
        results = search_script("repop_manager")
        if not results:
            return
        manager = results[0]
        spawn_id = self.db.spawn_id
        if spawn_id:
            manager.notify_death(str(spawn_id))
            return
        scout_id = self.db.scout_id
        if scout_id:
            player = self._responsible_player()
            player_key = str(getattr(player, "id", "") or "") or None
            manager.notify_scout_death(str(scout_id), player_key)

    def apply_damage(self, amount: int) -> None:
        hp = self.traits.hp  # type: ignore[union-attr]
        was_alive = not is_dead(int(hp.value))
        hp.current = max(0, int(hp.value) - amount)
        if was_alive and is_dead(int(hp.value)):
            self.at_death()

    def at_aggro(self, character: object) -> None:
        """Announce this mob's attack; called when faction standing warrants aggression."""
        char_key = getattr(character, "key", "intruder")
        if self.location:
            self.location.msg_contents(
                f"{self.key} attacks {char_key}!",
                exclude=[],
            )

    def aggro_check(self, character: object) -> None:
        """Look up faction standing and call at_aggro if standing is hostile or kill-on-sight.

        Skips silently when no faction_id is set or no faction_manager script exists.
        Morale check (R8/R5) is a future revision; for now KOS and hostile always aggro.
        """
        faction_id: object = self.db.faction_id
        if not faction_id:
            return
        results = search_script("faction_manager")
        if not results:
            return
        mgr = results[0]
        player_key = str(getattr(character, "id", "") or "")
        if not player_key:
            return
        band: str = mgr.standing_band(str(faction_id), player_key)
        if band in ("hostile", "kill-on-sight"):
            self.at_aggro(character)


class ServiceNpc(Mob):
    """Peaceful static Keep NPC: tavernkeeper, Curate, chapel staff.

    Carries a short rpsystem-style ``sdesc`` and a human-readable ``role``; it
    never aggresses (the Keep is a no-combat zone — it sets no ``faction_id``,
    so the inherited ``aggro_check`` is a no-op). The disguised-priest plot
    (M12) draws its seasonal spy from the chapel-staff ServiceNpcs the builder
    tags ``priest_pool``.
    """

    IS_SERVICE_NPC: bool = True

    def at_object_creation(self) -> None:
        super().at_object_creation()
        self.db.npc_key = ""  # stable zone identity (e.g. "tavernkeeper")
        self.db.sdesc = ""  # short description shown before identification
        self.db.role = ""  # human-readable function (e.g. "almoner")


class Henchman(Mob):
    """AI follower hired from the Keep tavern (docs/specs/henchmen.md §5).

    The employer holds a reference in db.employer; the henchman's current
    standing order lives in db.order (default "follow").
    """

    IS_HENCHMAN: bool = True

    def at_object_creation(self) -> None:
        super().at_object_creation()
        self.db.employer = None  # PlayerCharacter who hired this henchman
        self.db.order = "follow"  # standing order (henchmen.md §5)
        self.db.loyalty = 7  # seeded at hire; adjusted by event table (§2)
        self.db.own_target = None  # active when order == "attack"

    def at_death(self) -> None:
        """Permadeath: drop gear to corpse, free party slot, delete (henchmen.md §6)."""
        loc = self.location
        if loc:
            loc.msg_contents(f"{self.key} has been slain!", exclude=[])
            if self.contents:
                corpse = create.create_object(
                    "typeclasses.objects.Corpse",
                    key=f"corpse of {self.key}",
                    location=loc,
                )
                corpse.db.owner_key = self.key
                for item in list(self.contents):
                    item.move_to(corpse, quiet=True)
                    item.home = loc
        self.delete()


class TargetDummy(Mob):
    """Non-aggressive training dummy for testing the attack command.

    Fixed stats: AC 10, HP 100, no attack bonus, morale 12 (never flees).
    Calls super().at_object_creation() then force-replaces the HP trait so the
    gauge starts at 100 rather than the Mob default of 1.
    """

    def at_object_creation(self) -> None:
        super().at_object_creation()
        # force=True (the default) removes the old hp trait before re-adding,
        # so current starts fresh at base=100 with no stale stored value.
        self.traits.add("hp", "Hit Points", trait_type="gauge", base=100, mod=0)
