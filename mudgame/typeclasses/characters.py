"""PlayerCharacter typeclass with OSE stats wired via the traits contrib."""

from __future__ import annotations

from evennia.contrib.rpg.traits import TraitHandler
from evennia.objects.objects import DefaultCharacter
from evennia.utils import lazy_property

from world.rules.abilities import ability_modifier
from world.rules.combat import armor_class

from .objects import ObjectParent


class PlayerCharacter(ObjectParent, DefaultCharacter):
    """Player-controlled character with OSE ability scores, HP, AC, XP, and level."""

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
        # Single source of truth for the AC formula (armor/shield default to 0
        # until the clothing-contrib equipment lands).
        return armor_class(dex_modifier=ability_modifier(dex_score))

    def apply_damage(self, amount: int) -> None:
        hp = self.traits.hp  # type: ignore[union-attr]
        hp.current = max(0, int(hp.value) - amount)


# Keep the name Evennia expects for the default character typeclass.
Character = PlayerCharacter
