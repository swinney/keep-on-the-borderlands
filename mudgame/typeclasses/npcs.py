"""Mob typeclass for monsters and NPCs with OSE stats wired via the traits contrib."""

from __future__ import annotations

from evennia.contrib.rpg.traits import TraitHandler
from evennia.objects.objects import DefaultCharacter
from evennia.utils import lazy_property

from world.rules.abilities import ability_modifier
from world.rules.combat import is_dead

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

    @property
    def computed_ac(self) -> int:
        dex_score: int = int(self.traits.dex.value)  # type: ignore[union-attr]
        return 10 + ability_modifier(dex_score)

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
