"""PlayerCharacter typeclass with OSE stats wired via the traits contrib."""

from __future__ import annotations

import evennia
from evennia.contrib.rpg.traits import TraitHandler
from evennia.objects.objects import DefaultCharacter
from evennia.server.models import ServerConfig
from evennia.utils import create, lazy_property, logger
from evennia.utils.search import search_object_by_tag, search_script

from world.economy import secure_treasure
from world.rules.abilities import ability_modifier
from world.rules.combat import armor_class, is_dead
from world.rules.henchmen import henchman_should_follow
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
        # Payload of a spell declared this combat round (combat.md §4.1/§5),
        # resolved at end of round by the CombatHandler: {"spell": .., "target": ..}.
        self.db.pending_cast: dict[str, str] | None = None
        # Back-reference to the CombatHandler driving the caster's current fight;
        # set by add_combatant so `cast` knows to declare-and-resolve, not cast
        # synchronously. None outside combat.
        self.db.combat_handler = None
        self.db.coin: int = 0
        self.db.bank_balance: int = 0
        # Lifetime gp already converted to XP via XP-on-secure (economy.md §6).
        self.db.secured_xp_credited: int = 0
        self.db.hardcore: bool = False
        # Per-character quest log (quests.md §1); keyed by quest id. See
        # world.quests.state for the entry shape and the pure state machine.
        self.db.quests: dict[str, object] = {}

        # Spawn at the recall point (the Inner Bailey, CLAUDE.md §2 / zones/keep.md).
        # Evennia's default creation leaves location at START_LOCATION, which this
        # project does not set, so without this a freshly `create`d character has
        # no location and is unreachable. Only fill an *unset* location, and only
        # when the Inner Bailey exists (its recall tag is present once the world is
        # built): this preserves a location explicitly passed to create_object(),
        # and is a no-op for the God character created during at_initial_setup,
        # before the Keep is built (it keeps its default Limbo placement).
        # (`home` is intentionally not set: Evennia overwrites it with DEFAULT_HOME
        # after this hook, and recall uses the inner_bailey tag via
        # _find_recall_room, not `home`.)
        if self.location is None:
            recall_rooms = search_object_by_tag("inner_bailey")
            if recall_rooms:
                self.location = recall_rooms[0]

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

        # The season_manager owns the leaderboard (death.md §10: this path only
        # *writes* the fell entry; the mechanics live with seasonal reset, R6).
        # It stamps the season + timestamp itself. In a running game the manager
        # always exists; if it is somehow absent, log loudly rather than silently
        # losing a permadeath record.
        managers = search_script("season_manager")
        if managers:
            managers[0].record_fell(name, class_name, final_level)
            season = managers[0].db.season_number
        else:
            season = ServerConfig.objects.conf("current_season", default=1) or 1
            logger.log_err(
                f"season_manager not found; hardcore fell entry for {name} "
                f"(L{final_level}, season {season}) was NOT recorded on the leaderboard"
            )

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

    def at_post_move(self, source_location: object | None, **kwargs: object) -> None:
        """After moving: trigger mob aggro and move following henchmen."""
        super().at_post_move(source_location, **kwargs)
        if self.location is None:
            return
        # Carrying coin alive into a Keep room secures it → XP-on-secure (economy.md §6).
        if self.location.db.zone == "keep":
            secure_treasure(self)
        for obj in list(self.location.contents):
            if getattr(obj, "IS_MOB", False) and callable(getattr(obj, "aggro_check", None)):
                obj.aggro_check(self)
        if source_location is not None:
            for obj in list(source_location.contents):
                if (
                    getattr(obj, "IS_HENCHMAN", False)
                    and obj.db.employer == self
                    and henchman_should_follow(str(obj.db.order or ""))
                ):
                    obj.move_to(self.location, quiet=True)

    def apply_damage(self, amount: int) -> None:
        hp = self.traits.hp  # type: ignore[union-attr]
        was_alive = not is_dead(int(hp.value))
        hp.current = max(0, int(hp.value) - amount)
        # Disrupt any in-progress spell declaration (combat.md §5): a caster who
        # declared a spell this round (in combat) but takes damage before the
        # CombatHandler resolves it loses the prepared slot with no effect.
        declaring: str | None = self.db.spell_declaring
        if declaring:
            memorized: list[str] = list(self.db.memorized_spells or [])
            if declaring in memorized:
                memorized.remove(declaring)
                self.db.memorized_spells = memorized
            self.db.spell_declaring = None
            self.db.pending_cast = None
            self.db.spell_disrupted = True
            self.msg(f"Your {declaring} spell is disrupted!")
        if was_alive and is_dead(int(hp.value)):
            self.at_death()


# Keep the name Evennia expects for the default character typeclass.
Character = PlayerCharacter
