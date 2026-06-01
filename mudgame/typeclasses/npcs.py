"""Mob typeclass for monsters and NPCs with OSE stats wired via the traits contrib."""

from __future__ import annotations

from evennia.contrib.rpg.traits import TraitHandler
from evennia.objects.objects import DefaultCharacter
from evennia.utils import create, lazy_property
from evennia.utils.search import search_script

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

    @property
    def computed_ac(self) -> int:
        dex_score: int = int(self.traits.dex.value)  # type: ignore[union-attr]
        # Single source of truth for the AC formula (matches PlayerCharacter).
        return armor_class(dex_modifier=ability_modifier(dex_score))

    def at_death(self) -> None:
        """Death handoff stub — M3/M5 expand this to XP award + loot (combat.md §4.2)."""
        if self.location:
            self.location.msg_contents(f"{self.key} has been slain!", exclude=[])

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
