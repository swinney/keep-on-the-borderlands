"""PlayerCharacter typeclass with OSE stats wired via the traits contrib."""

from __future__ import annotations

from datetime import UTC, datetime

import evennia
from evennia.contrib.rpg.traits import TraitHandler
from evennia.objects.objects import DefaultCharacter
from evennia.server.models import ServerConfig
from evennia.utils import create, lazy_property
from evennia.utils.search import search_object_by_tag

from world.leaderboard import append_fell
from world.rules.abilities import ability_modifier
from world.rules.combat import armor_class, is_dead
from world.rules.progression import xp_for_level
from world.rules.saves import CharacterClass

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
        self.db.spellbook: list[str] = []
        self.db.memorized_spells: list[str] = []
        self.db.spell_declaring: str | None = None
        self.db.spell_disrupted: bool = False
        self.db.coin: int = 0
        self.db.bank_balance: int = 0
        self.db.hardcore: bool = False

    @property
    def computed_ac(self) -> int:
        dex_score: int = int(self.traits.dex.value)  # type: ignore[union-attr]
        # Single source of truth for the AC formula (armor/shield default to 0
        # until the clothing-contrib equipment lands).
        return armor_class(dex_modifier=ability_modifier(dex_score))

    @property
    def hardcore(self) -> bool:
        """Whether this character is on the irrevocable hardcore path (death.md §4)."""
        return bool(self.db.hardcore)

    @hardcore.setter
    def hardcore(self, value: bool) -> None:
        # Irrevocable (death.md §4): the flag may be turned ON (opt-in at
        # creation) but never cleared. An attempt to set it False is ignored.
        if value:
            self.db.hardcore = True

    def enable_hardcore(self) -> None:
        """Opt this character into hardcore permadeath at creation. Irrevocable."""
        self.hardcore = True

    def get_display_name(self, looker: object | None = None, **kwargs: object) -> str:
        """Prefix a `[HC]` marker for hardcore characters (who-list/title, death.md §4)."""
        name: str = super().get_display_name(looker, **kwargs)
        return f"[HC] {name}" if self.hardcore else name

    def _create_corpse(self) -> None:
        """Create a Corpse in the current room holding all gear and carried coin."""
        if not self.location:
            return
        corpse = create.create_object(
            "typeclasses.objects.Corpse",
            key=f"corpse of {self.key}",
            location=self.location,
        )
        corpse.db.owner_key = self.key
        for item in list(self.contents):
            item.move_to(corpse, quiet=True)
            # Re-home gear to the death room: the owner may be deleted
            # (hardcore), and items must not reference a tombstoned home or
            # any later relocation/cleanup will raise ObjectDoesNotExist.
            item.home = self.location
        corpse.db.coin = self.db.coin or 0
        self.db.coin = 0

    def _find_recall_room(self) -> object | None:
        """Return the Inner Bailey recall room, falling back to home."""
        rooms = search_object_by_tag("inner_bailey")
        if rooms:
            return rooms[0]
        return self.home

    def _resolve_char_class(self) -> CharacterClass | None:
        """Coerce the stored char_class to a CharacterClass enum, or None.

        `db.char_class` is stored as a string (the enum *value*, e.g.
        ``"fighter"``) by the game's creation/spell code, so coerce it the same
        way `commands/spells.py` does. An already-resolved enum passes through
        unchanged; an unset or unrecognized value yields None.
        """
        raw = self.db.char_class
        if raw is None:
            return None
        try:
            return CharacterClass(raw)
        except ValueError:
            return None

    def _default_death(self) -> None:
        """XP loss to level start + recall to Inner Bailey at 1 HP (specs/death.md §2)."""
        char_class = self._resolve_char_class()
        if char_class is not None:
            current_level = int(self.traits.level.value)  # type: ignore[union-attr]
            threshold = xp_for_level(char_class, current_level)
            current_xp = int(self.traits.xp.current)  # type: ignore[union-attr]
            if current_xp > threshold:
                self.traits.xp.current = threshold  # type: ignore[union-attr]
        recall_room = self._find_recall_room()
        if recall_room is not None:
            self.move_to(recall_room, quiet=True)
        self.traits.hp.current = 1  # type: ignore[union-attr]
        self.db.memorized_spells = []

    def _hardcore_death(self) -> None:
        """Leaderboard entry + broadcast + deletion (specs/death.md §3)."""
        name = self.key
        char_class = self._resolve_char_class()
        if char_class is not None:
            class_name = char_class.value
        elif isinstance(self.db.char_class, str) and self.db.char_class:
            class_name = self.db.char_class
        else:
            class_name = "unknown"
        final_level = int(self.traits.level.value)  # type: ignore[union-attr]
        season: int = ServerConfig.objects.conf("current_season", default=1) or 1

        entry: dict[str, object] = {
            "name": name,
            "class": class_name,
            "level": final_level,
            "season": season,
            "recorded_at": datetime.now(tz=UTC).isoformat(),
        }
        append_fell(entry)

        message = f"{name} the {class_name} has fallen at level {final_level}, season {season}."
        if evennia.SESSION_HANDLER is not None:
            for session in evennia.SESSION_HANDLER.get_sessions():
                session.msg(message)

        self.delete()

    def at_death(self) -> None:
        """Full death dispatch (specs/death.md §1)."""
        if self.location:
            self.location.msg_contents(f"{self.key} has been slain!", exclude=[])
        self._create_corpse()
        if self.hardcore:
            self._hardcore_death()
        else:
            self._default_death()

    def apply_damage(self, amount: int) -> None:
        hp = self.traits.hp  # type: ignore[union-attr]
        was_alive = not is_dead(int(hp.value))
        hp.current = max(0, int(hp.value) - amount)
        # Disrupt any in-progress spell declaration (combat.md §5).
        # NOTE: currently inert — synchronous `cast` never sets spell_declaring.
        # Real disruption needs combat-round declare/resolve timing; deferred,
        # see tasks.md "Spell disruption via combat-round timing".
        declaring: str | None = self.db.spell_declaring
        if declaring:
            memorized: list[str] = list(self.db.memorized_spells or [])
            if declaring in memorized:
                memorized.remove(declaring)
                self.db.memorized_spells = memorized
            self.db.spell_declaring = None
            self.db.spell_disrupted = True
            self.msg(f"Your {declaring} spell is disrupted!")
        if was_alive and is_dead(int(hp.value)):
            self.at_death()


# Keep the name Evennia expects for the default character typeclass.
Character = PlayerCharacter
