# Rejected Alternatives

Relocated from `CLAUDE.md` §9. Captured so future-Claude doesn't re-litigate
settled choices. These are *not* ADRs (no single decision/date); they're the
standing "considered and rejected" list backing the locked decisions in
`CLAUDE.md` §2. The numbered ADRs (`0001`–`0003`) cover decisions made *after*
this list.

- **ROM / Diku C codebase.** Rejected: dev velocity disaster with
  Claude as builder.
- **CoffeeMUD (Java).** Worth a look but Evennia's Python ecosystem
  is a better fit for Claude Code maintenance.
- **Custom MUD from scratch in Rust/Go.** Always tempting, almost
  always wrong. Rejected.
- **AD&D 1e rules.** Rejected: B2 was written for B/X; 1e tripled
  the rule surface for no real fidelity gain.
- **Emergent simulated factions** (tribes have AI goals, simulate
  on a tick). Rejected for v1: too much code, too many bug surfaces
  for a Ralph Loop. Scripted states are the testable middle ground.
- **Standard Diku 15-min total repop.** Rejected: kills the political
  layer that makes B2 worth adapting.
- **Per-player instancing of the disguised Priest.** Rejected: breaks
  shared-world illusion.
- **PvP in v1.** Deferred: complexity vs payoff doesn't pencil at
  this scale.
- **Forced grouping.** Rejected: kills MUDs at low population.
  Henchmen solve the problem.
