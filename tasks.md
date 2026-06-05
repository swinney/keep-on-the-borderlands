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
- [x] Season-global effects (expose priest, destroy Shrine); `tests/quests` green (M13 exit)
- [x] M13 review-fix (PR #20): **per-quest evidence threshold**. Today `commands/quests` gates every `requires_evidence` quest on one global `can_report` boolean (1 strong proof OR 3 sightings), but `cu_suspicions` must open at **≥2 clue sightings** (priest `CURATE_CLUE_THRESHOLD`) while `c_expose_priest` needs report-grade. Give the `Quest` record a per-quest evidence requirement (e.g. an `evidence_min` field: report-grade vs curate-threshold) and evaluate it per quest. Update `tests/quests` to pin both thresholds.
- [x] M13 review-fix (PR #20): **grant `Reward.items` on turn-in**. `_apply_reward` applies only gp/xp + faction effects and ignores `quest.reward.items` (holy water, map, relic — spec §9.3). Append each item to the caller's inventory (`caller.db.quest_items` list). Add a `tests/quests` case proving an item-reward quest delivers its items.
- [x] M13 review-fix (PR #20): **close the deed-quest turn-in exploit**. `qstate.steps_met` is vacuously true for deed-only quests (no kill steps), and `turnin` checks nothing else, so a deed quest can be accepted and turned in instantly for full reward/effects without the deed (e.g. deliver-rations, destroy-Altar). Gate deed-only turn-in behind a **deed-completion flag** on the quest entry that only a world event sets; `turnin` refuses until it is set. EXCEPTION: a quest whose deed *is* the turn-in action — `c_expose_priest` (reporting to the Castellan) — stays gated by its evidence requirement, not a prior flag. For `c_destroy_shrine`: do **not** fire `end_season` from the quest turn-in (the `Altar.at_destruction` hook is the canonical R6 trigger, per review F4); gate its turn-in on a shrine-destroyed marker and grant only the reward. Rewrite `tests/quests/test_season_global.py` (which currently turns in `c_destroy_shrine` with no deed) accordingly and add a refused-without-deed test.
- [x] ⛔ MILESTONE GATE (M13 → M14) — **passed**: M13 reviewed and merged via PR #20 (CI green; Copilot's 5 findings addressed — F2 per-quest evidence threshold, F5 item rewards, F3 deed-quest turn-in exploit, F4 destroy-shrine→Altar-only `end_season`; F1 giver-key resolution deferred-and-documented). Built free-run by the loop (turns 57–64) with a review-driven gap-closure round.

## M14 — Polish & scale

Buildable now (static config — no runtime needed):

- [x] Web-client theming + MOTD
- [x] ⛔ MILESTONE GATE (M14 polish slice → review) — **passed**: web-client theming + MOTD reviewed and merged via PR #21 (CI green; Copilot's 3 nits addressed — STATUS phrasing, order-independent file reads, exact-tag template assertions). Built free-run by the loop (turns 65–66, Sonnet). The remaining M14 criteria are BLOCKED on the world-build/runtime layer below.

The remaining three M14 acceptance criteria — economy/XP balance, 50-player
<100ms latency, and full acceptance-criteria verification — are **BLOCKED on the
world-build/runtime layer**: they need a *playable, load-testable* server, which
the no-op spawner / absent world-build precludes. They are tracked under M15
below (and "Deferred follow-ups" → *World-build / runtime orchestrator*) and
become doable once that phase lands. They are deliberately **not** loop-grabbable
tasks until then.

## M15 — World bring-up (runtime orchestrator)

The phase the deferrals have been pointing at: make the game actually *run* a
populated world. This unblocks the M13 quest-giver/deed-event wiring and the
three blocked M14 acceptance criteria. **Spec-first** — the spec is pivotal, so
the loop drafts it and halts for review before any tests/implementation.

- [x] Spec: write `docs/specs/world-build.md` — the runtime world-build/boot orchestrator (spawner, giver-key, deed hooks, bootable server). Spec only; no implementation.
- [x] ⛔ MILESTONE GATE (M15 spec → review) — **passed**: spec reviewed and approved (operator-gated; commit 4af1c8a). Every factual claim verified against the live code (MobRecord/SpawnPoint shapes, Mob death→repop back-ref, season_manager reset ordering, register_zone/spawn_points, empty at_initial_setup); design preserves the managers→build→zones dependency direction, respects all locked decisions, and resolves M13 F1/F3/F4. Implementation slices (spec §14) below.

Implementation slices (spec §14, each spec→test→impl, dependency order):

- [x] M15 slice 1 — `world/build/templates.py`: pure mob-template registry aggregating every zone's `MOB_TEMPLATES` into `template_key → MobRecord` (globally-unique keys, `KeyError` on unknown); `tests/world_build/test_templates.py` (pure, Django-free). Per spec §5, §13.1.
- [x] M15 slice 2 — `world/build/spawner.py`: `spawn_mob`/`spawn_scout`/`despawn` materializing a `MobRecord`+room into a live `Mob` (seeded-RNG HP roll, faction_id/is_leader/spawn_id wired), with spawn-instance-tag idempotency (§6-§7); rewire `repop_manager._instantiate*`/`_retreat_scout`/`_reset_shrine` restock to delegate; `tests/world_build/test_spawner.py`. Per spec §13.2-§13.3, §13.6.
- [x] M15 slice 3 — `world/build/orchestrator.py` `build_all()`: zone build order + manager bring-up + spawn registration + initial population pass, idempotent; wire `at_initial_setup()`; `tests/world_build/test_orchestrator.py` (incl. idempotency §13.4 + leadership-halt-with-real-scouts integration §13.5).
- [x] M15 slice 4 — giver-key (M13 F1): add `giver_key` to `NpcRecord`/`MobRecord`, builder + spawner write-through, `commands.quests._giver_here` resolves on `db.giver_key`; tribe-chief alive-and-present rule; `tests/world_build/test_givers.py` (§13.7).
- [x] M15 slice 5 — deed hooks (M13 F3): `world/build/events.py` + the in-world triggers (altar shrine-destroyed flag WITHOUT re-firing `end_season`, delivery/escort/spy-drop); `tests/world_build/test_deed_hooks.py` (§13.8).
- [x] M15 slice 6 — season-rebuild delegation (`rebuild_world`→orchestrator, despawn-stale→repopulate, persistence untouched) + the boot/headless-population check + load-harness sketch; unblocks the three M14 measurement tasks. Per spec §10-§11, §13.9-§13.10.
- [x] M15 fix (full-suite regression): `tests/zones/test_shrine_build.py::test_destroying_altar_ends_the_season` **errors in teardown** on the full suite. The test body passes (the season ends), but `end_season` now triggers the real `rebuild_world` → `orchestrator.build_all()`, which rebuilds the **entire** world (keep+wilderness+caves+shrine) mid-test; the shrine-only fixture then leaks the other zones and its teardown crashes (`ObjectDoesNotExist: Hosting object was already deleted`) on the now cross-referenced object graph. The `end_season → rebuild_world` behavior is **correct** (seasonal-reset spec) — do NOT change it. Fix the **test**: make its setup/teardown consistent with the world-rebuild side effect (build the full world via `world.build.orchestrator.build_all()` in the fixture so setup↔teardown are symmetric, and/or tear down every zone's rooms/exits/objects defensively — tolerating already-deleted objects), while preserving the season-end assertion. **Run the FULL `pytest` suite** (not subsets) and confirm 0 errors/failures before committing — slice 6 gated on subsets and missed this.
- [x] M15 review-fix (PR #22, Copilot's 3 findings): (F1) `world/build/templates.py` — `all_templates`/`get_template` rebuild the registry on every call, so `build_all` re-scans every zone's `MOB_TEMPLATES` once per spawn point. Memoize the aggregated `template_key → MobRecord` map at module level and return a **copy** (prevent accidental mutation); keep the duplicate-key integrity check. (F2) `world/build/loadharness.py` — `run_load` proceeds when the `inner_bailey` recall room is missing, creating `location=None` loadbots yet still reporting `driven_sessions == requested_sessions`, masking a failed/partial build. Detect the missing recall room and report honestly (drive nothing, surface the unbuilt world in the `LoadReport`/raise) — spec §11 "report, not silently cap." (F3, real wiring gap not just docs) `typeclasses/npcs.py` — `Mob.at_death` only calls `repop_manager.notify_death(spawn_id)`; a scout carries `scout_id` (not `spawn_id`), so a killed scout never notifies the manager though `notify_scout_death` exists and the spawner docstring claims it does. Wire `at_death` to call `notify_scout_death(scout_id, ...)` when the mob is a scout, so scout kills update scouting state. Add/extend `tests/world_build` for all three; **run the FULL `pytest` suite** before committing.
- [x] ⛔ MILESTONE GATE (M15 → review) — **passed**: world bring-up reviewed and merged via PR #22 (CI green; Copilot's 3 findings addressed — F1 template-registry memoization, F2 honest load-harness on unbuilt world, F3 real scout-death→notify_scout_death wiring gap; plus a review-caught full-suite regression fixed in `e28e213`). Built free-run by the loop (turns 67–79, Opus), spec-first with an operator spec-review gate. **PAUSED here before M16 per operator instruction.**

## M16 — Acceptance & scale (the M14 criteria, unblocked by M15)

M15 made the game **runnable + populated**, so the three M14 acceptance criteria
that were blocked on a runtime are now doable. These are measurement/tuning/
verification (not new content), so M16 is **spec-first** with an operator
spec-review gate before implementation — the approach (how to measure latency,
how to project/tune XP pacing, how to demonstrate acceptance) is the part worth
reviewing.

- [x] Spec: write `docs/specs/acceptance.md` — how M16 delivers the three M14 criteria against the live runtime: (1) **50-player <100ms latency** via the M15 load harness (`world.build.loadharness.run_load`) — drive 50 synthetic sessions through `build_all`'s populated world, assert a p95/max command latency target, honest report (`recall_built`); (2) **economy/XP-pacing balance** (`economy.md`) — a deterministic projection/simulation of a representative play arc reaching ~L10 in a 6-week season, tuning the economy/XP constants to hit it, pinned by a test; (3) **full acceptance verification** — enumerate the OpenSpec/build-plan acceptance criteria and demonstrate each is met (test-backed checklist). Define a `tests/acceptance/` plan. Per PROMPT.md, write the spec and stop — no implementation this turn.
- [x] ⛔ MILESTONE GATE (M16 spec → review) — **passed**: spec reviewed and approved (operator-gated; commit c5e74ad). Honest about proxies — C8 is server-side per-command latency in-process (not a wire-level 50-socket test; telnet deferred per ADR 0005), pacing is a deterministic projection (not a 6-week playtest), verification is a test-existence checklist; respects locked decisions (no OSE-table retune, no new content) and bakes in guard ⑤ (escalate if a criterion is unmet, never fudge the budget). Referenced proof suites + pacing knobs verified to exist. Slices (spec §7) below.

Implementation slices (spec §7, each spec→test→impl, dependency order):

- [x] M16 slice 1 — XP-pacing projection: `world/rules/pacing.py` (pure, no Evennia) — a deterministic `project_arc(char_class, arc) → ArcResult` over the existing cores (`economy.secure_xp` treasure-as-XP + OSE kill-XP, resolved via `progression.level_for_xp`), with the representative-arc + target-band as **named constants**. Tune ONLY the economy/pacing knobs (`economy.py` sinks, `pacing.py` arc constants) to land the target band (~L9–L10 for a representative class over a 6-week season); never retune the OSE XP table. `tests/acceptance/test_xp_pacing.py` pins the final level + per-week curve (regression-guard) and asserts the OSE thresholds are untouched. Pure, Django-free. Per spec §3, §6.2-§6.3.
- [x] M16 slice 2 — C8 latency measurement: `tests/acceptance/test_latency_50.py` (engine) drives `loadharness.run_load(50)` against `build_all()`'s populated world; asserts honesty (`recall_built`, `driven_sessions==50`, `commands_run==50*len(mix)`, populated world) AND `latency.p95_ms`/`max_ms` under named budgets set from an observed baseline with margin under 100ms. If the observed p95 exceeds 100ms the criterion is UNMET — escalate via `docs/questions.md`, do NOT weaken the budget (spec §2.4, CLAUDE.md §3). Per spec §2, §6.1.
- [x] M16 slice 3 — criteria-coverage checklist: `tests/acceptance/test_criteria_coverage.py` encodes the §4 C1–C8 table as data (criterion → proof test node ids) and asserts each mapped proof test exists and is collectable (all eight mapped; a renamed/removed proof fails the test). References existing suites, does not re-run/duplicate them. The capstone declaring v1 acceptance demonstrably met. Per spec §4, §6.4.
- [x] M16 fix (CI failure): `tests/acceptance/test_latency_50.py` FAILED on the CI runner — `assert max_ms < 90` got **141ms** (p95 passed at ~3.7ms locally; the single MAX sample spiked on GitHub's shared runner). Asserting *max* latency is brittle on noisy infra — latency SLOs are p50/p95/p99, never worst-case-ever. Fix robustly (NOT by fudging the budget): (a) add a **warmup** to `world.build.loadharness.run_load` (drive a few commands before timing, so cold-start/import/JIT cost isn't sampled) and exclude warmup from `LoadReport.latency`; (b) make **p95 the gating criterion assertion** (`p95_ms < P95_BUDGET_MS`, budget under the 100ms criterion with margin) — p95 ~3.7ms genuinely meets `<100ms`; (c) **report max but do not gate on a tight max budget** (drop `MAX_BUDGET_MS` or assert only a loose anti-hang sanity bound, documented), since max is infra-dominated. Update `docs/specs/acceptance.md` §2 to record the warmup + p95-as-criterion choice honestly. If p95 itself exceeds 100ms that is a real unmet criterion → escalate (CLAUDE.md §3). Verify the FULL suite locally, but note the real check is CI green on re-push (the failure is CI-runner-specific). Also: `tests/acceptance/conftest.py` joins the deferred "Django-free pure tests in mixed dirs" cross-cutting follow-up (Copilot PR #22 F2) — do NOT diverge one conftest now.
- [x] ⛔ MILESTONE GATE (M16 → review) — **passed**: acceptance & scale reviewed and merged via PR #23 (CI green after a CI-runner-only latency-max flake was fixed via warmup + p95-gating; Copilot F1 false-positive pushed back, F2 folded into the deferred conftest item). Built free-run by the loop (turns 80–86, Opus), spec-first. **v1 ACCEPTANCE DEMONSTRABLY MET** — all eight OpenSpec criteria C1–C8 machine-checked (`tests/acceptance/test_criteria_coverage.py`).

## M17 — Deferred polish & hardening (post-v1, optional)

v1 acceptance is met (M16); these are the deferred-follow-up items, now driven
one per branch/PR for focused review. Each is `spec(exists)→test→impl`, gated.

- [x] M17a — **Django-free conftests**: gate the `scope="session", autouse=True` Evennia bootstrap to `@pytest.mark.django_db` tests across **all** engine conftests (`tests/quests`, `tests/zones`, `tests/economy`, `tests/world_build`, `tests/acceptance`), so a pure test (e.g. `test_xp_pacing.py`) run in isolation does NOT boot Django (verify with `pytest --setup-show` on a pure test) while full-suite runs stay green. The fix should be uniform (don't diverge one conftest). Then check off the matching Deferred-follow-ups item. Per the deferred note (Copilot PR #8, #22 F2).
- [x] ⛔ MILESTONE GATE (M17a → review) — **passed**: merged via PR #24 (CI green; Copilot's 3 docstring nits fixed inline). Engine conftests now gate the Evennia bootstrap to sessions containing a `@pytest.mark.django_db` test — pure tests run Django-free in isolation (verified: isolated pure run 0.5s, no init). Built by the loop on Sonnet (turn 87).

## M17b — Spell disruption via combat-round timing (combat.md §5)

- [x] Make `cast` **declare** a spell (set `spell_declaring`) and resolve it at end of round via the `CombatHandler`, so damage taken before resolution disrupts it (combat.md §5). M2 shipped the inert `apply_damage` hook (synchronous casting never declares); this needs the round loop's declare→resolve phases. Re-enable the skipped `tests/combat/test_combat.py::test_damage_disrupts_unresolved_cast`. Then check off the matching Deferred-follow-ups item. spec→test→impl; full-suite green before commit.
- [x] M17b review-fix (PR #25, Copilot's 4 findings): (F1–F3) in `typeclasses/scripts.py`, `add_combatant`/`remove_combatant`/`at_stop` only set/clear `combatant.db.combat_handler` `if combatant.attributes.has("combat_handler")` — so a character created before this PR (no such Attribute) never gets the back-ref and `_in_combat` mis-reports, casting synchronously in combat. Remove the guards and **set/clear `db.combat_handler` unconditionally** (Evennia Attributes can be assigned freely; works for new and pre-existing characters). Add an engine test that a combatant whose `combat_handler` Attribute was deleted still declares in combat after `add_combatant`. (F4) in `commands/spells.py`, in-combat `cast` overwrites `db.spell_declaring`/`db.pending_cast` even if a spell is already declared this round — silently dropping the first declaration (its reserved slot never resolves or disrupts). Refuse a second in-combat cast while one is pending ("You are already casting <spell> this round.") preserving the first declaration; add a test. Full suite green before commit.
- [x] ⛔ MILESTONE GATE (M17b → review) — **passed**: merged via PR #25 (CI green; Copilot's 4 findings fixed via the loop — F1–F3 unconditional `combat_handler` back-ref for pre-existing characters, F4 single-declaration-per-round guard). In-combat `cast` now declares and resolves at end of round; damage disrupts. Re-enabled `test_damage_disrupts_unresolved_cast`. Built by the loop on Opus (turns 88–90).

## M17c — Installation & run guide + README refresh (operator-facing docs)

The repo has **no guide for running the game** — only the Ralph-Loop dev-container README, and the root README is stale ("pre-alpha, no game code yet" when the game is v1-acceptance-complete). M15 made the game runnable, so a real guide is now writeable.

- [x] Write `docs/installation.md` (linked from README + docs/index.md): a complete, **verified** operator guide to install and run the actual MUD — prerequisites (Python ≥3.12), install (`pip install -e .` per pyproject), DB migrate (`evennia migrate`), first-boot world population (`at_initial_setup()` → `world.build.orchestrator.build_all()` runs on first `evennia start`; note how to (re)populate an existing DB), starting the server (`evennia start`), and connecting (telnet host:4000 + the web client URL, with the M16 theming/MOTD). Ground EVERY command in the real entry points (don't invent flags); where a step can't be auto-verified here, say so. Then **refresh `README.md`**: change the status from "pre-alpha / no game code" to v1-acceptance-complete (M0–M16 + the M17 polish), add a "Run the game" section linking the new guide, and keep the "Run the build loop" (Ralph) section clearly separated. Docs-only; ruff/mypy/pytest unaffected — but the guide's commands must be accurate.
- [x] ⛔ MILESTONE GATE (M17c → review) — **passed**: merged via PR #26 (CI green; operator-verified the guide's commands against the tree — caught + fixed two doc-rot errors, incl. one Copilot also flagged: theme description and the `server/logs/` path). `docs/installation.md` written, README destaled to v1-acceptance-complete, docs nav updated. Built by the loop on Opus (turn 92).

## Deferred follow-ups

- [x] **World-build / runtime orchestrator** ⭐ — **DELIVERED by M15** (PR #22):
  the boot orchestrator builds + spawns + serves a populated world, quest-givers
  resolve by `giver_key` (M13 F1), world-event deed hooks fire (M13 F3), season
  rebuild repopulates, and a headless boot + load-harness ship. Residual, still
  open: the **M16 acceptance criteria** (above) and the carrier-object deed
  triggers (delivery/escort/spy-package) + the live-spy `giver_key` stamping —
  content-frozen seams whose hooks exist and are tested, awaiting their carrier
  objects/relocation wiring (tracked below).

- [x] **Spell disruption via combat-round timing** (combat.md §5): make `cast`
  *declare* a spell (set `spell_declaring`) and resolve it at end of round via
  the `CombatHandler`, so damage taken before resolution disrupts it. M2 shipped
  the `apply_damage` hook but left it inert (synchronous casting never declares);
  this needs the round loop's declare→resolve phases. Re-enables the skipped
  `tests/combat/test_combat.py::test_damage_disrupts_unresolved_cast`.
  **DELIVERED by M17b.**

- [x] **Pure tests run Django-free in mixed dirs** (Copilot PR #8, #22 F2): the
  `scope="session", autouse=True` bootstrap in the engine conftests (`tests/quests`,
  `tests/zones`, `tests/economy`, `tests/world_build`, `tests/acceptance`) pulls
  `django_db_setup` into the *pure* tests in those dirs (e.g. `test_xp_pacing.py`),
  so running one in isolation boots Evennia (verified via `pytest --setup-show`).
  Full-suite runs are unaffected. Fix consistently across all engine conftests
  (gate the bootstrap to `@pytest.mark.django_db` tests) rather than diverging one
  — a cross-cutting test-infra change, deferred from M9. **DELIVERED by M17a.**

- [ ] **Quest runtime — giver resolution + deed-completion event hooks**
  (deferred from M13; depends on the spawner/world-build layer). Two pieces, both
  blocked on live NPCs/world events that don't exist yet:
  - **Giver resolution (review F1).** `commands.quests._giver_here` matches an NPC
    by `db.role` against `GIVERS`, but `role` is a display descriptor for most
    NPCs (the spy's chapel role is `almoner`/etc., the hermit, the provisioner) —
    only the Guildmaster and Castellan happen to have `role == giver-key`. So the
    `HERMIT`/`SPY`/`PROVISIONER` and tribe-chief (`t_*`, plain `Mob`s) givers are
    unreachable: their quests can't be listed/accepted/turned in. Give giver NPCs
    an explicit quest-giver key (separate from display `role`) and resolve on that;
    decide how a tribe-chief turn-in works (a chief you may also be there to kill).
  - **Deed-completion event hooks.** M13 gates deed-only quest turn-in behind a
    deed-completion flag, but the *world events that SET it* are deferred — e.g.
    `Altar.at_destruction` → shrine-destroyed marker (the altar already fires
    `end_season`), "rations delivered", "captive escorted home", spy-package
    drop-offs. Wire each deed's trigger when the spawner/world-build lands.
  The completion *effects* themselves (`tension_pair`/`aid_faction`/
  `breaks_alliance`/cult chain/`reward.items`) are wired + tested at the wiring
  level in `tests/quests/test_quests.py`. Also correct the stale "24 quests" prose
  in `docs/specs/quests.md` and `docs/build-plan.md` — the §2–§7 tables enumerate
  **26**, which is what M13 wired.

---

When every box above is checked, the loop writes "RALPH: project complete" to
`STATUS.md` and exits (`PROMPT.md` stop condition).
