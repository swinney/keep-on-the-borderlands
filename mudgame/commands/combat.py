"""Combat commands: attack.

docs/specs/combat.md §4 (combat round) and §4.1 (attack resolution / damage).
The attack command resolves one melee attack against a target in the caller's
room using OSE ascending-AC rules from world.rules.combat.  Dice are rolled via
random.Random so tests can patch the class; pure resolution logic lives in the
rules layer.
"""

from __future__ import annotations

import random
from typing import ClassVar

from evennia.commands.command import Command

from world.rules import dice
from world.rules.abilities import ability_modifier
from world.rules.combat import attack_hits, melee_damage

_DEFAULT_WEAPON_SIDES = 6


class CmdAttack(Command):  # type: ignore[misc]
    """Strike a target in your current room.

    Usage:
      attack <target>

    Resolves one melee attack using OSE ascending-AC rules.  A natural 20
    always hits; a natural 1 always misses.  Without equipped weapons the
    damage die is 1d6 (placeholder until the equipment system lands in a later
    milestone).
    """

    key = "attack"
    aliases: ClassVar[list[str]] = ["kill", "hit"]
    help_category = "Combat"

    def parse(self) -> None:
        self.target_name = self.args.strip()

    def func(self) -> None:
        caller = self.caller
        if not self.target_name:
            caller.msg("Attack what?")
            return

        target = caller.search(self.target_name, location=caller.location)
        if not target:
            return

        if target is caller:
            caller.msg("You can't attack yourself.")
            return

        if not (hasattr(target, "traits") and hasattr(target, "apply_damage")):
            caller.msg(f"You can't attack {target.key}.")
            return

        # Record the aggressor so the target's death can credit faction standing
        # to the right player (faction.md §2.1); set on any swing, not just hits,
        # so the last attacker is known regardless of the killing blow's roll.
        if target.attributes.has("last_attacker"):
            target.db.last_attacker = caller

        # Roll through the dice seam (centralised notation/validation); pure
        # resolution below consumes the rolled values.
        rng = random.Random()
        d20 = dice.roll("1d20", rng=rng)
        weapon_roll = dice.roll(f"1d{_DEFAULT_WEAPON_SIDES}", rng=rng)

        str_score: int = int(caller.traits.str.value)
        str_mod = ability_modifier(str_score)
        atk_bonus: int = int(caller.traits.attack_bonus.value)
        target_ac: int = target.computed_ac

        hit = attack_hits(
            d20=d20,
            attack_bonus=atk_bonus,
            ability_modifier=str_mod,
            target_ac=target_ac,
        )

        if hit:
            dmg = melee_damage(weapon_roll=weapon_roll, str_modifier=str_mod)
            target.apply_damage(dmg)
            caller.location.msg_contents(
                f"{caller.key} hits {target.key} for {dmg} damage!",
                exclude=[],
            )
        else:
            caller.location.msg_contents(
                f"{caller.key} misses {target.key}!",
                exclude=[],
            )
