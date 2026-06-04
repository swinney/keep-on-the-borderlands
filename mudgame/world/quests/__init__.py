"""Quest subsystem (docs/specs/quests.md).

M9 shipped the vertical-slice subset — the Guildmaster's tribe-clearing bounty
(`g_kobold_cull`) wired end to end. M13 fills in the full B2 catalog: every quest
across all givers (Castellan, Curate, Guildmaster, Provisioner, Hermit, the tribe
chiefs, and the rotating disguised priest), with their prerequisites, rewards, and
cross-system effects (faction standing/tension, the cult-aiding chain, and the two
season-global quests).

Layout mirrors the other subsystems (faction/, repop/, season/): pure, Evennia
-free data and logic live here —

* ``config`` — the quest catalog and its tuning constants (one balance file).
* ``state`` — the per-character quest state machine (plain dicts, unit-tested
  without booting the server).

The Evennia wiring (the Guildmaster commands, kill-step crediting on mob death,
reward payout) lives in ``commands.quests`` and ``typeclasses.npcs``.
"""
