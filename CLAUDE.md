# Keep on the Borderlands MUD — Project Memory

Cold-start contract for any fresh Claude session. Read end-to-end before
acting. This file is **always-loaded**, so it stays lean: locked decisions and
patterns live here; deep rationale, strategy, and specs are linked and read on
demand. Decisions in §2 and patterns in §3 are **locked** — do not reopen
without explicit user input.

**Map of where things live:**
- Full spec corpus → `docs/specs/` (per-subsystem) + `docs/architecture.md`
- Ralph Loop strategy + container ops → `docs/ralph-loop.md`
- Phased build plan (milestones) → `docs/build-plan.md`
- OpenSpec prompt (already executed) → `keep-on-borderlands-openspec-prompt.md` + `openspec/`
- Resolved open questions → `docs/open-questions.md`; escalations → `docs/questions.md`
- Decision records → `docs/decisions/` (ADRs `0001`–`0004`, `rejected-alternatives.md`)
- Ralph Loop field log (lifecycle / retrospective) → `docs/ralph-loop-experiment.md`
- Last loop-exit reason → `STATUS.md`

---

## 1. Project Overview

An **open-source persistent multiplayer text MUD** adapting module **B2: The
Keep on the Borderlands** (Gygax, 1979) as the opening campaign arc of a larger
D&D-flavored MUD.

- **Audience:** classic-MUD / old-school-D&D players. **Surface:** telnet +
  Evennia web client. **Scale:** 20–50 concurrent players in B2 content.
- **Built by Claude Code via a Ralph Loop** (iterative spec → test → implement
  → refine). Spec quality and testability are first-class.
- **Host:** development and runtime on a Linux machine.

---

## 2. Locked Decisions

Settled through deliberate discussion. Rationale kept terse; the fuller
"considered and rejected" backing is in `docs/decisions/rejected-alternatives.md`.

- **Engine: Evennia (Python 3, Django ORM).** Modern stack, mature MUD
  primitives, real web client, large contrib ecosystem. C (ROM/Diku) rejected:
  dev-velocity disaster with Claude as maintainer. **Use contribs aggressively**
  (`traits`, `rpsystem`, `combat`, `clothing`, etc.); override only where OSE
  demands. Document every contrib used/rejected in `docs/decisions/`.
- **License: MIT.** Open source for maximum adoption (resolved from the
  MIT/Apache/AGPL question; see `docs/open-questions.md`). `LICENSE` + `pyproject`
  already reflect this.
- **Ruleset: Old School Essentials (OSE)** — B/X retroclone (Moldvay/Cook).
  B2 was written for B/X, OSE's SRD text is openly licensed, ~⅓ the rule surface
  of AD&D 1e. Race-as-class (Dwarf, Elf, Halfling). Classes: Cleric, Fighter,
  Magic-User, Thief + the three race-classes. No multiclass in v1.
- **Level range for B2 content: 1–10** (MUD-scaled from the module's 1–3).
  Content past the Shrine is out of scope for v1 but not ruled out
  architecturally.
- **World persistence: seasonal resets** (6-week seasons; resolved). **Persists:**
  characters, XP, gear, bank, leaderboard. **Resets:** faction states, repop
  counters, Shrine state, disguised-Priest identity + clues, season-global quest
  effects. Full persistence is a content treadmill; total Diku repop kills the
  political layer.
- **Faction system: scripted states.** Per tribe-pair state ∈ {allied, peaceful,
  tense, war}; per (faction, player) standing ∈ {friendly, neutral, hostile,
  kill-on-sight}. Rule-based threshold transitions (not full simulation), all
  thresholds in one config file. Initial pair-states mirror the module. Scripted
  is reactive yet testable — important for loop convergence. Spec:
  `docs/specs/faction.md`.
- **Solo viability: henchmen.** Hire from a Keep tavern roster (canon to B2).
  AI NPCs that follow, fight, demand XP/treasure share; OSE loyalty/morale; flee
  or refuse below thresholds; per-character cap; permadeath. Spec:
  `docs/specs/henchmen.md`.
- **Death penalty (default): XP loss + corpse run.** Lose XP to start of current
  level; corpse persists at death location with gear, retrievable by walking
  back.
- **Death penalty (hardcore, opt-in, irrevocable): permadeath + leaderboard.**
  Character deleted on death; final level + season added to a server-wide
  leaderboard (per-season *and* all-time; resolved). Visually flagged (title,
  who-list marker). Spec: `docs/specs/death.md`.
- **Disguised Priest plot: rotating identity.** Each season the evil-priest spy
  is randomly assigned to one of N chapel NPCs with clues drawn from a pool;
  no back-to-back identity repeat. Offers Shrine-aiding quests (3+ → scripted
  Caves ambush). Detection: high-level Detect Evil, Curate dialogue, witnessing
  a nighttime act, finding a planted object. Reporting to the Castellan triggers
  a server-global "exposed" event (spy flees to Shrine, becomes a boss). Resets
  at season boundary. Rotating sidesteps "first player wins forever" without
  per-player instancing. Spec: `docs/specs/disguised-priest.md`.
- **PvP: disabled in v1.** Large edge-case cost, little payoff at this scale.
  Easy to add later.
- **Repop: tribe-scoped.** Standard mobs respawn 15 min. Killing a tribe's chief
  AND shaman halts that tribe's repop for 60 real min; during the dead window a
  rival tribe sends scouting parties into the empty caves and its faction-pair
  state may shift. Shrine resets on a 24-hour cycle with a server broadcast.
  Spec: `docs/specs/repop.md`.
- **Recall point: Inner Bailey of the Keep.**
- **No GM tooling in v1.** Build the systems, see what emerges, decide later.

**Resolved open questions** (full reasoning in `docs/open-questions.md`):
license=MIT, season=6 weeks, leaderboard=both, henchmen cap=OSE CHA table,
AC=**ascending** (player-friendly), Cave of the Unknown=sealed v1 stub,
economy=OSE treasure-as-XP with XP-on-secure, web client=default + light theming.

---

## 3. Architectural Patterns (Locked)

### Spec-Test-Implement, Strictly Enforced

What makes the Ralph Loop converge. Every subsystem (faction, repop, quests,
combat, henchmen, seasonal reset, disguised Priest, death penalty, etc.) requires:

1. A written spec in `docs/specs/<system>.md`.
2. A unit test suite in `tests/<system>/` derived from the spec.
3. An implementation that passes those tests.

**No implementation begins on a subsystem before its spec and test scaffold
exist.** Non-negotiable.

### Other locked patterns

- **Type safety:** `mypy --strict` on all custom modules. Type hints everywhere.
- **Lint:** `ruff` with sensible defaults.
- **Modular zones:** each zone is its own package under `world/zones/`, not a
  monolith — the loop works one zone without breaking another.
- **Persistence:** Evennia's Django ORM for player/world state; flat files only
  for static area definitions.
- **Repository conventions:**
  - One subsystem per commit; commit messages reference the task ID.
  - Never modify another subsystem's tests to make your code pass.
  - Modify specs only with explicit user input; otherwise modify the
    implementation to match the spec, or escalate via `docs/questions.md`.

The structural realization of these patterns (Evennia layout, contrib map,
pure `world/rules/` core, the four global-Script managers, persistence model) is
`docs/architecture.md`.

---

## 4. OpenSpec Prompt

The full proposal/requirements prompt that generated the Phase 0 corpus is
preserved verbatim at `keep-on-borderlands-openspec-prompt.md`; the executed
result is the `b2-mud-v1-design` change under `openspec/`.

## 5. Ralph Loop Strategy

Phase order, build order, the `PROMPT.md` template, the loop-runner script, and
hard-earned operational tips: **`docs/ralph-loop.md`** §1–§6. The
milestone-mapped build plan is `docs/build-plan.md`.

## 6. Container Setup (Linux Host)

The Ralph Loop runs inside Podman to bound `--dangerously-skip-permissions`.
Runtime decision + rationale: `docs/decisions/0001-container-runtime.md`.
Operational how-to (hybrid dev model, run command, network hardening):
`docs/ralph-loop.md` §7. Build artifacts: `Containerfile`, `Makefile`. Scaffolding
view: `docs/specs/scaffolding.md`.

## 7. Bootstrap / Phase 1

Phase 0 (specs) is complete. The Phase 1 bootstrap checklist (what to add:
`evennia --init mudgame`, pin Evennia, expand mypy scope, `PROMPT.md`, generate
root `tasks.md`) is `docs/specs/scaffolding.md` §6, with milestone M0 in
`docs/build-plan.md`.

## 8. Open Questions

All Phase 0 open questions are resolved with reasoning in
`docs/open-questions.md` (summary in §2 above). Live escalations from the loop
go to `docs/questions.md` (currently no blockers).

## 9. Things Considered and Rejected

`docs/decisions/rejected-alternatives.md` (ROM/Diku C, CoffeeMUD, from-scratch
Rust/Go, AD&D 1e, emergent factions, total Diku repop, priest instancing, v1
PvP, forced grouping).

---

## 10. Quick-Start for a Fresh Claude Session

1. Read this file end-to-end. §2 decisions and §3 patterns are **locked**.
2. Check `STATUS.md` for the last loop-exit reason / current phase.
3. Check `docs/specs/` for the spec corpus, `tasks.md` (once Phase 1 generates
   it) for task state, and `docs/questions.md` for blockers.
4. The full design depth is in `docs/` — load only what the current task needs
   (keeps context lean and prompt-caches stable).
5. When in doubt, ask the user — don't invent requirements.
