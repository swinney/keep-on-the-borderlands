"""Spell commands: cast, rest.

docs/specs/combat.md §5: Vancian memorization-on-rest, one slot per cast,
interruption on damage.  Pure spell logic lives in world.rules.spells; this
module handles player interaction, target resolution, and effect application.
"""

from __future__ import annotations

import random
from typing import Any, ClassVar

from evennia.commands.command import Command

from world.rules.saves import CharacterClass
from world.rules.spells import SpellData, get_spell, is_caster, spell_slots_for_level


class CmdCast(Command):  # type: ignore[misc]
    """Cast a memorized spell.

    Usage:
      cast <spell name>
      cast <spell name> at <target>
      cast <spell name> <target>

    Targeted spells (magic missile, cure light wounds) require a target name.
    Untargeted spells (light, detect evil) affect the caster's location.
    """

    key = "cast"
    aliases: ClassVar[list[str]] = []
    help_category = "Combat"

    def parse(self) -> None:
        self._raw = self.args.strip().lower()

    def func(self) -> None:
        caller = self.caller
        raw = self._raw

        if not raw:
            caller.msg("Cast what spell?")
            return

        # Split on " at " if present; otherwise spell name may include a target word.
        if " at " in raw:
            spell_part, target_part = raw.split(" at ", 1)
        else:
            spell_part = raw
            target_part = ""

        # Greedy spell-name match: try the longest possible prefix first so
        # multi-word spell names (e.g. "cure light wounds") take priority.
        words = spell_part.split()
        spell: SpellData | None = None
        spell_name = ""
        leftover = ""
        for end in range(len(words), 0, -1):
            candidate = " ".join(words[:end])
            try:
                spell = get_spell(candidate)
                spell_name = candidate
                leftover = " ".join(words[end:])
                break
            except KeyError:
                continue

        if spell is None:
            caller.msg(f"Unknown spell '{spell_part}'.")
            return

        target_name = (leftover + " " + target_part).strip()

        # Validate memorized
        memorized: list[str] = list(caller.db.memorized_spells or [])
        if spell_name not in memorized:
            caller.msg(f"You have not memorized {spell.name}.")
            return

        # Consume the slot (must happen before resolution in case of self-damage)
        memorized.remove(spell_name)
        caller.db.memorized_spells = memorized

        _resolve_spell(caller, spell, target_name)


class CmdRest(Command):  # type: ignore[misc]
    """Rest to recover and memorize spells.

    Usage:
      rest

    Casters fill their spell slots from their spellbook (Magic-User / Elf) or
    from the full divine list (Cleric).  Non-casters simply rest.
    """

    key = "rest"
    aliases: ClassVar[list[str]] = ["memorize", "pray"]
    help_category = "General"

    def parse(self) -> None:
        pass

    def func(self) -> None:
        caller = self.caller
        char_class_value: str | None = caller.db.char_class

        if not char_class_value:
            caller.msg("You rest briefly.")
            return

        try:
            char_class = CharacterClass(char_class_value)
        except ValueError:
            caller.msg("You rest briefly.")
            return

        if not is_caster(char_class):
            caller.msg("You rest briefly.")
            return

        level = int(caller.traits.level.value)
        slots = spell_slots_for_level(char_class, level)

        spellbook: list[str] = list(caller.db.spellbook or [])

        # Fill memorized_spells up to slot limits per spell level.
        memorized: list[str] = []
        for spell_level_idx, slot_count in enumerate(slots):
            spell_level = spell_level_idx + 1
            available = [s for s in spellbook if _safe_get_level(s) == spell_level]
            for i in range(slot_count):
                if available:
                    memorized.append(available[i % len(available)])

        caller.db.memorized_spells = memorized

        if memorized:
            caller.msg(f"You rest and prepare your spells: {', '.join(memorized)}.")
        else:
            caller.msg("You rest. (No spells to memorize at your current level.)")


# ── Helpers ────────────────────────────────────────────────────────────────────


def _safe_get_level(spell_name: str) -> int:
    """Return spell level or 0 if the name is unknown."""
    try:
        return get_spell(spell_name).level
    except KeyError:
        return 0


def _resolve_spell(caller: Any, spell: SpellData, target_name: str) -> None:
    """Dispatch to the appropriate effect handler."""
    if spell.name == "light":
        _cast_light(caller)
    elif spell.name == "magic missile":
        _cast_magic_missile(caller, target_name)
    elif spell.name == "cure light wounds":
        _cast_cure_light_wounds(caller, target_name)
    elif spell.name == "detect evil":
        _cast_detect_evil(caller)
    else:
        caller.msg(f"The {spell.name} spell fizzles. (Effect not yet implemented.)")


def _cast_light(caller: Any) -> None:
    loc = caller.location
    if loc:
        loc.db.light_spell = True
        loc.msg_contents(
            f"{caller.key} casts Light, filling the area with magical radiance!",
            exclude=[],
        )
    else:
        caller.msg("Light blazes around you.")


def _cast_magic_missile(caller: Any, target_name: str) -> None:
    if not target_name:
        caller.msg("Cast magic missile at whom?")
        return
    target = caller.search(target_name, location=caller.location)
    if not target:
        return
    if not hasattr(target, "apply_damage"):
        caller.msg(f"You cannot target {target.key} with magic missile.")
        return
    rng = random.Random()
    damage = rng.randint(1, 6) + 1  # 1d6+1, always hits
    target.apply_damage(damage)
    if caller.location:
        caller.location.msg_contents(
            f"{caller.key}'s magic missile strikes {target.key} for {damage} damage!",
            exclude=[],
        )


def _cast_cure_light_wounds(caller: Any, target_name: str) -> None:
    if not target_name or target_name in ("me", "self", caller.key.lower()):
        target = caller
    else:
        target = caller.search(target_name, location=caller.location)
        if not target:
            return
    if not (hasattr(target, "traits") and hasattr(target.traits, "hp")):
        caller.msg(f"You cannot heal {target.key}.")
        return
    rng = random.Random()
    heal = rng.randint(1, 6) + 1  # 1d6+1
    hp = target.traits.hp
    current = int(hp.value)
    max_hp = int(hp.base)
    new_hp = min(max_hp, current + heal)
    hp.current = new_hp
    actual = new_hp - current
    if caller.location:
        caller.location.msg_contents(
            f"{caller.key} casts Cure Light Wounds on {target.key}, restoring {actual} HP.",
            exclude=[],
        )


def _cast_detect_evil(caller: Any) -> None:
    loc = caller.location
    if not loc:
        caller.msg("You detect no evil presence here.")
        return
    evil: list[str] = []
    for obj in loc.contents:
        if getattr(obj, "IS_EVIL", False) or obj.attributes.get("is_evil", False):
            evil.append(obj.key)
    if evil:
        caller.msg(f"You sense evil radiating from: {', '.join(evil)}.")
    else:
        caller.msg("You detect no evil presence here.")
