## Context

Greenfield adaptation of module B2 into a persistent multiplayer MUD on Evennia,
built by a Ralph Loop. Phase 0 produced the full specification corpus: an
architecture overview, nine subsystem specs (R1–R9) with testable scenarios and
skipped pytest stubs, five zone outlines, a quest catalog, resolved open
questions, a scaffolding plan, and the build plan. The depth lives in `docs/`;
this design records the cross-cutting decisions that bind the subsystems. See
`docs/architecture.md` for structure and `docs/specs/*` for per-system detail.

## Goals / Non-Goals

**Goals:**
- A spec → test → implementation corpus a Ralph Loop can converge against, with
  every OpenSpec scenario mapping to a test.
- OSE rules fidelity with the most test-dense math isolated in a pure,
  Evennia-free `world/rules/` core.
- Preserve B2's political layer (scripted factions, tribe-scoped repop, the
  rotating disguised priest) while keeping it bounded and testable.
- Solo viability via henchmen; no forced grouping.

**Non-Goals (v1):** PvP, GM tooling, crafting beyond the provisioner, player
housing, content past the Shrine, mobile-first UI, a custom web client.

## Decisions

- **Ascending AC** — single-comparison attack resolution; testable edges
  (nat-20/nat-1). `docs/architecture.md` §5.1.
- **Pure rules core** — `world/rules/` has no Evennia imports, so OSE math is
  unit-tested without booting Django. The key testability lever.
- **Four global-Script managers** (faction, repop, season, priest) own all
  mutable world state and scheduling; typeclasses call into them; they call into
  `rules/`. Persistence via Evennia Attributes (Django ORM).
- **Factions as dual signed integers** — per-player reputation and per-pair
  tension, banded by thresholds; all tuning in one config file. Enables the
  "shared-enemy thaw" as arithmetic. `docs/specs/faction.md`.
- **Leadership halt requires both leaders dead simultaneously** — makes
  "chief AND shaman" a real coordination objective. `docs/specs/repop.md`.
- **Disguised priest: per-character investigation, server-global one-time
  exposure, no back-to-back identity repeat** — solves "first player wins
  forever" without per-player instancing. `docs/specs/disguised-priest.md`.
- **XP-on-secure** — OSE treasure-as-XP (1 gp = 1 XP) realized when treasure is
  banked/returned, making the journey and corpse-run the risk loop.
  `docs/open-questions.md`.
- **6-week seasons; both per-season and all-time leaderboards.**
- **Cave of the Unknown = sealed v1 stub** — no canonical content; preserves the
  architecture without authoring cost.
- **Contrib map** — adopt traits/rpsystem/clothing/extended_room/xyzgrid/buffs/
  character_creator; lift turnbattle as a pattern; reject crafting/barter/
  procedural-wilderness. `docs/architecture.md` §2.
- **Per-tribe shaman adaptation** — each Caves tribe gets a shaman spawn (the
  module omits some) so the halt mechanic is uniform. `docs/specs/zones/caves.md`.

## Risks / Trade-offs

- **Gnarly stateful subsystems** (faction machine, seasonal reset, rotating
  priest) are the highest-bug-risk surfaces. Mitigation: implement behind the
  pure-rules boundary where possible and use a verification subagent to review
  implementation against spec (CLAUDE.md §5).
- **Evennia/Django test friction** — Django-coupled tests need `pytest-django`
  and the test DB; slower than pure tests. Mitigation: maximize logic in
  `world/rules/`; keep manager tests focused.
- **Economy balance** — XP-on-secure plus gold sinks must pace ~level 10 in six
  weeks; all values are tunable config, tuned at the M14 polish milestone.
- **50-player <100ms latency** (acceptance) — ticker-driven combat must stay
  efficient; measured at M14, not assumed.
- **The shaman adaptation** deviates from the printed module; recorded so it is a
  choice, not a silent change.
