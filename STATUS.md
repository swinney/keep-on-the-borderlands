M14 POLISH SLICE COMPLETE & MERGED (PR #21, merge commit 30e2648). The
statically-buildable scope of the project is now exhausted (M0–M13 + the M14
web-theming/MOTD slice). Nothing in progress.

What's on main: the full B2 systems + content (rules, combat, death, factions,
henchmen, repop/seasonal reset, Keep, Wilderness, all Caves, Shrine, disguised
priest, quest catalog) and now the web-client theme + branded MOTD. 719 tests
passing, ruff + mypy --strict clean.

⭐ THE BUILDABLE BOUNDARY — what remains needs a runtime that doesn't exist yet.
Recorded in tasks.md "Deferred follow-ups" → *World-build / runtime orchestrator*.
Mob/NPC spawning is a deliberate no-op, so no zone is live-populated; everything
that needs a running, populated, load-testable game stacks behind that one
missing layer:
  - quest-giver resolution by giver-key + tribe-chief turn-in (M13 F1), and the
    world-event hooks that set deed-completion flags (M13 F3);
  - the three BLOCKED M14 acceptance criteria: economy/XP balance (playtest
    data), 50-player <100ms latency (running server + load harness), and "all
    acceptance criteria demonstrably met" (end-to-end runnability).

Next (a distinct phase, ~"M15 world bring-up"): an orchestrator that builds every
zone, spawns mobs/NPCs/leaders from the registries, wires givers, and exposes a
bootable server — then the deferred effect-hooks and the M14 tuning/measurement
become doable. Until then the build holds at this boundary. Drive it via the loop
on an m15 branch when taken on.

Operating mode: loop-driven, walk-away — the operator answers no questions; the
session proceeds on its own recommendation (see memory: loop-autonomy-mandate).
