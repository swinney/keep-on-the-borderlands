"""Quest subsystem (docs/specs/quests.md).

M9 ships the vertical-slice subset: the Guildmaster's tribe-clearing bounty
(`g_kobold_cull`) wired end to end. The full 24-quest catalog and its
cross-system effects land in M13.

Layout mirrors the other subsystems (faction/, repop/, season/): pure, Evennia
-free data and logic live here —

* ``config`` — the quest catalog and its tuning constants (one balance file).
* ``state`` — the per-character quest state machine (plain dicts, unit-tested
  without booting the server).

The Evennia wiring (the Guildmaster commands, kill-step crediting on mob death,
reward payout) lives in ``commands.quests`` and ``typeclasses.npcs``.
"""
