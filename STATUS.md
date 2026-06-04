M11 COMPLETE & MERGED (PR #17, merge commit abcca82). M12 is the next milestone
and is cleared to start (the earlier do-not-auto-start hold was lifted
2026-06-03).

The Shrine of Evil Chaos is built (the first serial milestone after the fan-out
was set aside — promising idea, but the M10 implementation caused more problems
than it solved; serial-by-default now, fan-out available to recommend, not
auto-used): 16 temple rooms descending from the Black Gate to the Inner
Sanctum, dark/no_recall flags per spec, the inter-zone link wired both ways to
the Caves minotaur maze; the cult mob roster (sentries, acolytes, crypt undead,
adept-acolyte casters) and the Adept boss; the 24h reset cycle now restocking
the cult wholesale through the repop_manager; and the destructible Altar of Evil
Chaos firing season_manager.end_season on its killing blow. 619 tests passing,
ruff + mypy --strict clean.

Built serially in four spec→test→implement slices (rooms+exits, mobs+boss,
24h-reset wiring, altar→end_season), per docs/specs/zones/shrine.md. The
rogue/unreviewed M11 draft in ../kotb-wt/m10-orc was NOT used.

Next: M12 — the disguised
priest (priest_manager: seasonal rotation with no back-to-back repeat, clue
assignment, the four detection paths, the spy quest chain + Caves ambush,
exposure → the Shrine boss_lair boss, season reset). Build per
docs/specs/disguised-priest.md, serially. boss_lair already waits empty in the
Shrine for the exposed-priest boss.
