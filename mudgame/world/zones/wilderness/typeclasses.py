"""Wilderness room typeclass with wandering-encounter hook.

Importing Evennia is intentional here; this module is excluded from the
pure-data contract (wilderness spec §1: only xymap.py, mobs.py, spawns.py,
npcs.py carry no Evennia imports).
"""

from __future__ import annotations

import random as _random

from evennia.contrib.grid.xyzgrid.xyzroom import XYZRoom

# Roll ≤ this on 1d6 triggers an encounter (~17% per move, spec §9.2).
WILDERNESS_ENCOUNTER_CHANCE: int = 1


class WildernessRoom(XYZRoom):
    """XYZRoom subclass that rolls for wandering encounters on player entry."""

    def at_object_receive(self, obj: object, source_location: object, **kwargs: object) -> None:
        super().at_object_receive(obj, source_location, **kwargs)  # type: ignore[misc]
        from typeclasses.characters import PlayerCharacter  # noqa: PLC0415

        if not isinstance(obj, PlayerCharacter):
            return
        if self.db.safe:
            return
        if _random.randint(1, 6) <= WILDERNESS_ENCOUNTER_CHANCE:
            self._spawn_encounter()

    def _spawn_encounter(self) -> None:
        """Weighted-random mob spawn for a wandering encounter (spec §9.3-9.4)."""
        from evennia import create_object  # noqa: PLC0415

        from typeclasses.npcs import Mob  # noqa: PLC0415
        from world.zones.wilderness.mobs import ENCOUNTER_TABLE, MOB_TEMPLATES  # noqa: PLC0415

        if not ENCOUNTER_TABLE:
            return
        total_weight = sum(w for w, _ in ENCOUNTER_TABLE)
        roll = _random.randint(1, total_weight)
        cumulative = 0
        chosen_key = ENCOUNTER_TABLE[-1][1]
        for weight, mob_key in ENCOUNTER_TABLE:
            cumulative += weight
            if roll <= cumulative:
                chosen_key = mob_key
                break

        templates = {m["key"]: m for m in MOB_TEMPLATES}
        template = templates.get(chosen_key)
        if template is None:
            return

        mob = create_object(Mob, key=template["name"], location=self)
        mob.db.faction_id = template["faction"]
