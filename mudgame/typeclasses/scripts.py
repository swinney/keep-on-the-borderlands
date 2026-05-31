"""
Scripts

Scripts are powerful jacks-of-all-trades. They have no in-game
existence and can be used to represent persistent game systems in some
circumstances. Scripts can also have a time component that allows them
to "fire" regularly or a limited number of times.

There is generally no "tree" of Scripts inheriting from each other.
Rather, each script tends to inherit from the base Script class and
just overloads its hooks to have it perform its function.

"""

from __future__ import annotations

import contextlib
import random
from typing import Any

from evennia.scripts.scripts import DefaultScript

from world.rules.abilities import ability_modifier
from world.rules.combat import initiative_order, initiative_roll

_MIN_COMBATANTS = 2


class Script(DefaultScript):
    """
    This is the base TypeClass for all Scripts. Scripts describe
    all entities/systems without a physical existence in the game world
    that require database storage (like an economic system or
    combat tracker). They
    can also have a timer/ticker component.

    A script type is customized by redefining some or all of its hook
    methods and variables.

    * available properties (check docs for full listing, this could be
      outdated).

     key (string) - name of object
     name (string)- same as key
     aliases (list of strings) - aliases to the object. Will be saved
              to database as AliasDB entries but returned as strings.
     dbref (int, read-only) - unique #id-number. Also "id" can be used.
     date_created (string) - time stamp of object creation
     permissions (list of strings) - list of permission strings

     desc (string)      - optional description of script, shown in listings
     obj (Object)       - optional object that this script is connected to
                          and acts on (set automatically by obj.scripts.add())
     interval (int)     - how often script should run, in seconds. <0 turns
                          off ticker
     start_delay (bool) - if the script should start repeating right away or
                          wait self.interval seconds
     repeats (int)      - how many times the script should repeat before
                          stopping. 0 means infinite repeats
     persistent (bool)  - if script should survive a server shutdown or not
     is_active (bool)   - if script is currently running

    * Handlers

     locks - lock-handler: use locks.add() to add new lock strings
     db - attribute-handler: store/retrieve database attributes on this
                        self.db.myattr=val, val=self.db.myattr
     ndb - non-persistent attribute handler: same as db but does not
                        create a database entry when storing data

    * Helper methods

     create(key, **kwargs)
     start() - start script (this usually happens automatically at creation
               and obj.script.add() etc)
     stop()  - stop script, and delete it
     pause() - put the script on hold, until unpause() is called. If script
               is persistent, the pause state will survive a shutdown.
     unpause() - restart a previously paused script. The script will continue
                 from the paused timer (but at_start() will be called).
     time_until_next_repeat() - if a timed script (interval>0), returns time
                 until next tick

    * Hook methods (should also include self as the first argument):

     at_script_creation() - called only once, when an object of this
                            class is first created.
     is_valid() - is called to check if the script is valid to be running
                  at the current time. If is_valid() returns False, the running
                  script is stopped and removed from the game. You can use this
                  to check state changes (i.e. an script tracking some combat
                  stats at regular intervals is only valid to run while there is
                  actual combat going on).
      at_start() - Called every time the script is started, which for persistent
                  scripts is at least once every server start. Note that this is
                  unaffected by self.delay_start, which only delays the first
                  call to at_repeat().
      at_repeat() - Called every self.interval seconds. It will be called
                  immediately upon launch unless self.delay_start is True, which
                  will delay the first call of this method by self.interval
                  seconds. If self.interval==0, this method will never
                  be called.
      at_pause()
      at_stop() - Called as the script object is stopped and is about to be
                  removed from the game, e.g. because is_valid() returned False.
      at_script_delete()
      at_server_reload() - Called when server reloads. Can be used to
                  save temporary variables you want should survive a reload.
      at_server_shutdown() - called at a full server shutdown.
      at_server_start()

    """

    pass


class CombatHandler(DefaultScript):
    """Ticker-driven round loop for one combat encounter (§4, spec combat.md).

    One CombatHandler exists per active combat. It fires every 6 seconds,
    rolls individual initiative for all living combatants, announces the order,
    and stops itself when fewer than two combatants remain alive.
    """

    def at_script_creation(self) -> None:
        self.key = "combat_handler"
        self.desc = "Manages one combat encounter round loop."
        self.interval = 6
        self.persistent = True
        self.start_delay = True
        self.db.combatants = []

    def is_valid(self) -> bool:
        alive = [c for c in (self.db.combatants or []) if c and int(c.traits.hp.value) > 0]
        return len(alive) >= _MIN_COMBATANTS

    def add_combatant(self, combatant: Any) -> None:
        if combatant not in self.db.combatants:
            self.db.combatants.append(combatant)

    def remove_combatant(self, combatant: Any) -> None:
        with contextlib.suppress(ValueError):
            self.db.combatants.remove(combatant)

    def at_repeat(self) -> None:
        combatants: list[Any] = self.db.combatants or []
        alive = [c for c in combatants if c and int(c.traits.hp.value) > 0]
        if len(alive) < _MIN_COMBATANTS:
            self.stop()
            return

        rng = random.Random()
        entries: list[tuple[Any, int, int]] = []
        for combatant in alive:
            dex_score: int = int(combatant.traits.dex.value)
            dex_mod = ability_modifier(dex_score)
            d6 = rng.randint(1, 6)
            roll_val = initiative_roll(dex_modifier=dex_mod, d6=d6)
            entries.append((combatant, dex_mod, d6))

        ordered = initiative_order(entries)
        for combatant, dex_mod, d6 in ordered:
            roll_val = initiative_roll(dex_modifier=dex_mod, d6=d6)
            if combatant.location:
                combatant.location.msg_contents(
                    f"{combatant.key} acts (initiative {roll_val}).",
                    exclude=[],
                )
