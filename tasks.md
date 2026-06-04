# Tasks — Keep on the Borderlands MUD

The Ralph Loop's work list, generated from `docs/build-plan.md` (the locked,
milestone-mapped build order). Each unchecked `[ ]` item is intended to be **one
Claude Code session**: a spec→test→implementation slice per `PROMPT.md`.

## How the loop uses this file
- Pick the **first unchecked task**, top to bottom. Order matters — earlier
  milestones are dependencies of later ones.
- Phase 0 already wrote, for every subsystem, a spec (`docs/specs/`) and
  **skipped** test stubs (`tests/<system>/`). So most tasks are "unskip the
  relevant stubs → implement until green," not write-from-scratch.
- A task is `[x]` only when its full spec→test→implementation cycle is done and
  `ruff` + `mypy` + `pytest` are all green (`PROMPT.md` workflow step 7).
- Never weaken a spec or another system's tests to pass (CLAUDE.md §3).
- One subsystem per commit; reference the task/milestone in the message.

Milestone exit criteria and rationale live in `docs/build-plan.md`. Specs live
in `docs/specs/`. Architecture in `docs/architecture.md`.

---

## M0 — Bootstrap (Phase 1, human-run, pre-loop)

- [x] `evennia --init mudgame`; validate boot via `evennia migrate`
- [x] Pin `evennia` in `pyproject` `[project.dependencies]`; add `pytest-django` to dev extras
- [x] Document the per-milestone settings-wiring plan in `mudgame/server/conf/settings.py`
- [x] Harden `scripts/ralph.sh` stop condition to non-empty STATUS.md (`-s`)
- [x] Add `PROMPT.md`; empty `STATUS.md`; generate this `tasks.md` from the build plan
- [x] Confirm CI green with the game dir present (`mudgame/` ruff-excluded, out of mypy strict scope)

### M0 handoff notes for the loop (read before M1)
- **mypy scope:** `[tool.mypy].files` is still `["tests"]` and the Evennia/Django
  `ignore_missing_imports` override is still commented out — deliberately. Expand
  `files` to a first-party package the first time one is created (M1), and
  restore the override the first time first-party code imports `evennia`/`django`
  (M2). Doing either earlier breaks CI (missing path / unused-override warning).
- **ruff vs first-party code under `mudgame/`:** `mudgame/` is ruff-excluded as
  vendored Evennia output, but `world/rules/` etc. are *ours* and must be linted
  and type-checked. M1's first task resolves this: either narrow the ruff exclude
  to only Evennia-generated files, or place first-party packages so they are
  ruff-included. Decide and document in `docs/decisions/`.

---

## M1 — Rules core (pure, no Evennia)

- [x] Resolve the ruff-exclude / mypy-include boundary for first-party `world/rules/`; document in `docs/decisions/`; expand `[tool.mypy].files`
- [x] `dice`: parse/roll `NdM(+K)` with a seeded-RNG seam; `tests/combat/test_dice.py`
- [x] Ability scores + modifiers (OSE table); HP roll by class/HD (`abilities.py`, `progression.py`)
- [x] Ascending-AC attack math: to-hit, nat-20/nat-1 edges, damage application
- [x] Saving throws (OSE save categories by class/level)
- [x] XP thresholds + level lookup per class; morale (2d6 vs morale score)
- [x] All rules-level `tests/combat` scenarios green without booting Evennia (M1 exit)

## M2 — Combat on the engine

- [x] Restore the mypy `evennia.*`/`django.*` override; wire `pytest-django` (`DJANGO_SETTINGS_MODULE`) for engine tests
- [x] `Character`/`Mob` typeclasses; wire AC/HP/abilities onto traits
- [x] Ticker-driven round loop + individual initiative
- [x] `attack` command + a target-dummy mob
- [x] Minimal Vancian spells: light, magic missile, cure light wounds, detect evil; `cast` + memorization-on-rest
- [x] 0 HP triggers a death handoff stub; `tests/combat` engine scenarios green (M2 exit)

## M3 — Death & hardcore

- [x] Corpse object creation at death location with full gear
- [x] Default death: XP loss to start of current level; recall-revive at Inner Bailey
- [x] Hardcore: opt-in flag at creation (irrevocable), deletion on death, leaderboard `fell` entry
- [x] Who-list / title marker for hardcore characters; `tests/death` green (M3 exit)

- [x] ⛔ MILESTONE GATE (M3 → M4 review) — **passed**: M3 reviewed and merged via PR #3.

## M4 — Faction state machine

- [x] `world/factions/config.py`: tribes, initial pair-states, thresholds (single tuning file)
- [x] `faction_manager` global Script: per-player standing + per-pair tension bands
- [x] Event deltas (e.g. kill-count shifts) + decay over time
- [x] NPC aggression binding from standing; `consider` command
- [x] `tests/faction` green, incl. shared-enemy thaw arithmetic (M4 exit)

- [x] ⛔ MILESTONE GATE (M4 → M5 review) — **passed**: M4 reviewed and merged via PR #4.

## M5 — Henchmen

- [x] Tavern roster + hire flow (reaction roll, hire cost, CHA-table cap)
- [x] Follow + basic order commands; combat AI
- [x] Loyalty/morale: flee or refuse below threshold (OSE)
- [x] XP + treasure share; permadeath + re-hire; `tests/henchmen` green (M5 exit)

- [x] ⛔ MILESTONE GATE (M5 → M6 review) — **deferred**: M5 batched with M6 into a single review/PR at the M6→M7 gate (velocity strategy). M5 is green and complete.

## M6 — Repop + seasonal reset

- [x] Spawn-point registration + 15-min respawn
- [x] Leadership halt: chief AND shaman dead → 60-min repop freeze
- [x] Rival-tribe scouting into the dead window + faction-pair shift
- [x] Shrine 24h reset cycle + server broadcast
- [x] `season_manager`: orchestrate per-manager reset hooks; leaderboard snapshot; `end_season`
- [x] Persistence check: characters/XP/gear/bank survive reset; `tests/repop` + `tests/seasonal_reset` green (M6 exit)

- [x] ⛔ MILESTONE GATE (M5+M6 → M7 review) — **passed**: M5+M6 reviewed and merged via PR #5.

## M7 — Keep zone

- [x] Build `world/zones/keep/` rooms + exits (recall = Inner Bailey)
- [x] Provisioner shop + economy (starting gold, pricing, gold sinks); bank
- [x] Tavern henchman roster integration; chapel staff NPCs (priest pool placeholder)
- [x] Rest / spell memorization in the Keep; new character spawns→equips→hires→rests (M7 exit)

- [x] ⛔ MILESTONE GATE (M7 → M8 review) — **passed**: M7 reviewed and merged via PR #6.

## M8 — Wilderness zone

- [x] `world/zones/wilderness/` hex map on `xyzgrid`; travel commands
- [x] Wandering-encounter tables
- [x] Set-pieces: hermit, spider lair, mountain lions, raiders
- [x] Travel Keep → ravine mouth works end-to-end (M8 exit)

- [x] ⛔ MILESTONE GATE (M8 → M9 review) — **passed**: M8 reviewed and merged via PR #7.

## M9 — Kobold cave vertical slice ⭐ (critical integration milestone)

- [x] `world/zones/caves/` kobold lair rooms + kobold mobs
- [x] Kobold chief + shaman leaders wired to the M6 leadership-halt + rival scouting
- [x] Faction standing shifts observable in kobold behavior (ties M4 ↔ M9)
- [x] Guildmaster tribe-clearing quest + treasure→XP-on-secure loop
- [x] Integration test: spawn → equip → hire → travel → clear tribe → return → turn in → bank for XP (M9 exit)

- [x] ⛔ MILESTONE GATE (M9 → M10 review) — **passed**: M9 reviewed and merged via PR #8. M10 runs via the fan-out harness (PR #10; `docs/specs/fanout-harness.md`) — one clone+container per tribe, pooled (≤2), per-tribe PRs.

## M10 — Remaining caves

- [x] Orc Vile Rune + Orc Decapitator (the playable war rivalry) — PR #14
- [x] Goblins + ogre ally — PR #11
- [x] Hobgoblins (King Nardo) — PR #12
- [x] Bugbears — PR #13
- [x] Gnolls + owlbear — PR #15
- [x] Minotaur maze + Shrine passage; faction rivalries + repop halts fire under test (M10 exit) — PR #16

- [x] ⛔ MILESTONE GATE (M10 → M11 review) — **passed**: all caves built + the
  cross-tribe rivalry/repop-halt integration test green (576 tests). Built via the
  **fan-out harness, then set aside** — the parallelize-content *idea* is
  promising, but this implementation was net-negative at M10 scale (more problems
  than it solved), so it's serial-by-default now and the fan-out stays a
  recommendable-but-not-auto-used option pending a reworked harness. Clean tribes
  landed directly; orc/gnoll/minotaur were salvaged from the rogue orc loop's
  complete+green branch and landed serially through review. Retrospective:
  `docs/ralph-loop-experiment.md` §3 (M10) + §5.13–5.16. **M11+ build serially by
  default.**

## M11 — Shrine

- [x] `world/zones/shrine/` temple rooms; `no_recall` deep rooms
- [x] The Adept boss
- [x] 24h reset wired to the M6 cycle
- [x] Destructible altar → `end_season`; reset + season-end trigger tested (M11 exit)

- [x] ⛔ MILESTONE GATE (M11 → M12 review) — **passed**: merged via PR #17 (CI green, Copilot review addressed):
  Shrine zone built serially (16 rooms dark/no_recall, cult roster + the Adept
  boss, the 24h reset restocking the cult wholesale, the destructible altar
  firing `end_season`). Full suite green (619 passed), ruff + mypy --strict
  clean. Built per `docs/specs/zones/shrine.md`; the rogue M11 draft in the orc
  clone was *not* used. `boss_lair` is left unpopulated for the M12
  disguised-priest exposure plot.

## M12 — Disguised priest

- [x] `priest_manager`: seasonal rotation with no back-to-back identity repeat
- [x] Clue assignment from the pool
- [x] Four detection paths: Detect Evil, Curate dialogue, witnessed nighttime act, planted object
- [x] Spy quest chain (3+ → Caves ambush)
- [x] Exposure → server-global event → spy flees to Shrine boss
- [x] `tests/disguised_priest` green, incl. two-season-rotation scenario (M12 exit)
- [x] ⛔ MILESTONE GATE (M12 → M13) — **passed**: M12 reviewed and merged via PR #19 (CI green, Copilot review addressed — 1 real bug caught + fixed (exposure guard), 2 brittle tests de-coupled from the RNG, 1 stale docstring fixed, 1 spec-backed pushback on validate-evidence-matches-spy).

## M13 — Quest catalog

- [x] Wire all 24 quests across givers (Castellan, Curate, Guildmaster, Provisioner, Hermit, chiefs, priest)
- [x] Faction gating + repeatable/story state per character
- [ ] Season-global effects (expose priest, destroy Shrine); `tests/quests` green (M13 exit)
- [ ] ⛔ MILESTONE GATE (M13 → M14) — write "M13 complete — paused for review." to STATUS.md and stop. Make no code changes and do not check this box.

## M14 — Polish & scale

- [ ] Economy / XP-pacing balance pass (target ~L10 in a 6-week season)
- [ ] 50-player <100ms command-latency measurement (acceptance criterion)
- [ ] Web-client theming + MOTD
- [ ] Encounter-table tuning; all OpenSpec acceptance criteria demonstrably met (M14 exit)

## Deferred follow-ups

- [ ] **Spell disruption via combat-round timing** (combat.md §5): make `cast`
  *declare* a spell (set `spell_declaring`) and resolve it at end of round via
  the `CombatHandler`, so damage taken before resolution disrupts it. M2 shipped
  the `apply_damage` hook but left it inert (synchronous casting never declares);
  this needs the round loop's declare→resolve phases. Re-enables the skipped
  `tests/combat/test_combat.py::test_damage_disrupts_unresolved_cast`.

- [ ] **Pure tests run Django-free in mixed dirs** (Copilot PR #8): the
  `scope="session", autouse=True` bootstrap in the engine conftests (`tests/quests`,
  `tests/zones`, `tests/economy`) pulls `django_db_setup` into the *pure* tests in
  those dirs, so running one in isolation boots Evennia (verified via
  `pytest --setup-show`). Full-suite runs are unaffected. Fix consistently across
  all seven engine conftests (gate the bootstrap to `@pytest.mark.django_db` tests)
  rather than diverging one — a cross-cutting test-infra change, deferred from M9.

---

When every box above is checked, the loop writes "RALPH: project complete" to
`STATUS.md` and exits (`PROMPT.md` stop condition).
