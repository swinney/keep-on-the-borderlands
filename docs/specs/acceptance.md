# Acceptance & Scale Spec (M16) — delivering the three M14 criteria on the live runtime

M15 made the game **runnable and populated** (`docs/specs/world-build.md`): a
single `world.build.orchestrator.build_all()` boots every zone, brings up the four
managers, and spawns live mobs/leaders, and `world.build.loadharness.run_load`
drives synthetic sessions through the real cmdhandler. That unblocked the three
M14 acceptance criteria that were explicitly **blocked on a runtime** (`tasks.md`
M14): **50-player <100 ms latency**, **economy/XP-pacing balance**, and **full
acceptance-criteria verification**.

This spec defines **how M16 measures, tunes, and demonstrates** those three. It is
measurement/tuning/verification work, not new content: it adds no zone, mob, quest,
or rule, and reopens no locked decision (CLAUDE.md §2–§3). Per `PROMPT.md`, this
turn writes the spec only; the `tests/acceptance/` suite and any implementation
follow in later slices after the M16 spec-review gate.

The testable contract is §6; the slice plan is §7.

---

## 1. Scope and non-goals

**In scope (M16):**

1. **50-player <100 ms latency** (criterion C8). Drive 50 synthetic sessions
   through the M15 load harness against `build_all()`'s populated world, assert a
   p95/max per-command latency target, and report honestly (`recall_built`,
   requested-vs-driven) — surfacing an unbuilt/partial world rather than silently
   claiming success.
2. **Economy / XP-pacing balance** (criterion in `docs/specs/economy.md`,
   build-plan M14). A **deterministic projection** of a representative play arc
   reaching ~level 10 in a 6-week season, expressed against the pure rules core
   (`world/rules/progression.py`, `world/rules/economy.py`), with the economy/XP
   constants tuned to hit that target and the result pinned by a test.
3. **Full acceptance verification** (criterion: "all acceptance criteria in the
   OpenSpec prompt demonstrably met"). Enumerate the eight OpenSpec acceptance
   criteria (§4) and demonstrate each is met by a **test-backed checklist** that
   maps every criterion to the live test(s) that prove it.
4. A `tests/acceptance/` suite organized per §6, the home for the C8 measurement,
   the XP-pacing projection test, and the criteria-coverage checklist test.

**Out of scope (explicit non-goals):**

- No new content (zones/mobs/NPCs/quests) and no change to the pure rules core's
  **contracts** — only the *tuning constants* in the single economy file may move
  (§3.3), and only if the projection requires it. The XP thresholds in
  `progression.py` are OSE-SRD canon (CLAUDE.md §2 level range 1–10) and are
  **not** retuned; pacing is balanced via the economy knobs and the play-arc model,
  not by rewriting the SRD table.
- No live-network/telnet end-to-end harness: the C8 measurement uses the in-process
  transport already chosen in ADR 0005 (`docs/decisions/0005-load-harness-transport.md`);
  an external telnet driver stays the documented fallback for a true wire-level
  number and is not built here.
- No GM tooling (CLAUDE.md §2), no re-running of subsystem behavior already proven
  green in its own suite — the verification checklist **references** existing tests,
  it does not duplicate them.
- No reopening of any locked decision; a genuine contradiction or unspecified
  behavior is escalated via `docs/questions.md` (PROMPT.md), not invented here.

---

## 2. Criterion C8 — 50-player <100 ms command latency

### 2.1 What is measured

The OpenSpec criterion is "Server holds 50 concurrent players with <100 ms command
latency." M16 measures the quantity the M15 harness was built to produce:
**server-side per-command processing latency** — the time the engine spends in the
cmdhandler for one command, as timed by `loadharness.run_load` with
`time.perf_counter` around `Object.execute_cmd` (the same full cmdhandler path a
real session runs; `loadharness.py` docstring + ADR 0005). This deliberately
excludes network/portal transit (the in-process transport has none); per ADR 0005
that transit is the documented telnet-fallback's concern, and server-side
processing is the quantity the criterion constrains and the one we can measure
deterministically in CI.

### 2.2 The measurement

A single engine test in `tests/acceptance/` (pytest-django, Evennia test harness):

1. Calls `loadharness.run_load(50)` — which runs `build_all()`, connects 50
   synthetic `PlayerCharacter` loadbots at the recall point, drives each through
   the representative command mix (`DEFAULT_COMMAND_MIX`: read/move verbs), times
   every command, and tears the bots down.
2. Asserts the run was **honest and complete**: `report.recall_built is True`,
   `report.driven_sessions == 50`, and `report.commands_run == 50 * len(mix)` — so
   a partial/unbuilt world fails the test loudly instead of passing vacuously
   (world-build spec §11; the `recall_built=False` path exists precisely to make
   this detectable).
3. Asserts the **latency target**: `report.latency.p95_ms < P95_BUDGET_MS` and
   `report.latency.max_ms < MAX_BUDGET_MS`, with the budget(s) defined as named
   constants in the test module so the target is reviewable in one place.

### 2.3 Concurrency model and the honesty of the claim

The 50 sessions are driven **sequentially in one process**, not truly
simultaneously — this is the M15 transport (ADR 0005) and it is the right call for
a *deterministic, CI-runnable* measurement of per-command cost: it isolates the
server-side work per command from scheduler/IO noise. The criterion's word
"concurrent" is honored in the sense that matters for a single-threaded Evennia
twistd reactor — **50 players' worth of populated-world state is resident** (the
full `build_all()` world: every zone, every spawned mob/leader, all four managers'
state) while each command is processed, so each command pays the real cost of
resolving against a fully-populated world, not an empty one. The test asserts the
world is populated (mob/room counts > 0 via the harness build) so the latency is
measured against realistic state, not a bare grid.

This limitation is **stated, not hidden**: the test's docstring and the §5
checklist entry for C8 record that the number is single-process server-side
per-command latency against a fully-populated world, and that a true wire-level
concurrent-socket measurement is the ADR-0005 telnet fallback, deferred. "Report,
not silently cap" (world-build §11) is the governing principle — we report exactly
what was measured.

### 2.4 Budget choice

`P95_BUDGET_MS` and `MAX_BUDGET_MS` are set in the implementation slice from an
**observed baseline**: the slice first records the harness output for 50 sessions,
then sets the budget with comfortable headroom under the 100 ms criterion (e.g.
p95 well under 100 ms) so the test asserts the criterion is met with margin rather
than pinning a brittle exact figure. If the observed p95 is *not* under 100 ms, the
slice does not fudge the budget — it escalates (the criterion is unmet and that is a
finding, not a test to weaken; CLAUDE.md §3 "never weaken a spec/test to pass").
The chosen budget and the baseline it came from are recorded in the test module and
the §5 checklist.

---

## 3. Criterion — economy / XP-pacing balance to ~L10 in a 6-week season

### 3.1 The target

The locked design (CLAUDE.md §2: B2 level range 1–10; 6-week seasons) implies a
pacing goal: a representative player following the campaign's intended loop should
be able to reach roughly **level 10 over a 6-week season** — fast enough that the
cap is reachable, slow enough that it is not trivial. M16 makes this concrete and
testable as a **deterministic projection**, not a live playtest (a live 6-week run
is neither CI-runnable nor reproducible).

### 3.2 The projection model (pure, deterministic)

A new pure module `world/rules/pacing.py` (no Evennia import, unit-testable —
CLAUDE.md §3 / architecture §1) models a **representative play arc** as a
value-in/value-out function over the existing pure cores:

- **XP sources, per the specs already written:**
  - *Treasure-as-XP* (the campaign's primary source; `economy.md` §6): 1 gp of
    **secured** value = 1 XP, via `world.rules.economy.secure_xp`. The model sums
    the secured treasure of a representative clear-and-bank arc.
  - *Kill XP* (combat spec; additive): the OSE XP-by-HD award for the mobs cleared
    on that arc.
- **The arc** is a parameterized sequence of "encounters secured" (e.g. N tribe
  clears + quest turn-ins per week of a 6-week season), drawn from the content
  M9–M13 actually wired — the model reads representative treasure/kill values, it
  does not invent new numbers. The arc parameters (encounters/week, average secured
  gp per clear, average kill-XP per clear) are **named constants** in
  `pacing.py` so the single file documents the assumptions a reviewer checks.
- **The projection** `project_arc(char_class, arc) -> ArcResult` accumulates total
  XP across the arc and resolves the attained level via
  `world.rules.progression.level_for_xp` (the unmodified OSE table). `ArcResult`
  carries the per-week XP curve and the final level.

The model is **deterministic**: no RNG in the projection (averages, not rolls), so
the pacing test pins exact numbers and is reproducible. (The underlying rolls have
seeded-RNG seams already; the *pacing* layer uses expected values by design — a
balance projection, not a simulation of variance.)

### 3.3 Tuning to hit the target

The pacing test asserts the projected final level lands in the **target band** for
a representative class (e.g. Fighter reaches L9–L10 by end of season under the
modeled arc; the exact band is a named constant in `pacing.py`/the test). If the
projection misses:

- Tune **only** the economy/pacing knobs that are *designed to be tuning knobs*
  (CLAUDE.md §3 "thresholds in one config"; `economy.md` §7): the treasure award
  magnitudes / gold-sink constants in `world/rules/economy.py`
  (`BANK_DEPOSIT_FEE_PCT`, the secured-value assumptions), and the arc-shape
  constants in `pacing.py`. These are the legitimate pacing levers `economy.md` §7
  names ("because gold ≈ XP, every sink is also a pacing knob").
- **Do not** retune the OSE XP thresholds in `progression.py` (SRD canon) or change
  any pure-core *contract*. Tuning moves numbers within their single config file;
  it never rewrites a function's meaning.

The tuned constants and the resulting projected curve are pinned by the test, so a
later accidental change to a pacing knob breaks the pacing test — the balance is
**regression-guarded**, which is the durable deliverable (a one-off manual balance
pass would not survive future edits).

### 3.4 Why projection, not playtest

A 6-week live run cannot be a unit test. The projection is the testable surrogate:
it makes the pacing assumptions **explicit and reviewable** (the arc constants),
**deterministic** (expected values), and **regression-guarded** (pinned). It is
honest about being a model — the §5 checklist entry states the balance is
demonstrated by projection against the wired content's representative values, not
by a completed 6-week playthrough, and names the arc assumptions as the thing a
reviewer scrutinizes.

---

## 4. Full acceptance-criteria verification

The OpenSpec prompt lists eight testable acceptance criteria
(`keep-on-borderlands-openspec-prompt.md` §"Acceptance criteria"; mirrored in the
build-plan coverage map). M16's third deliverable is a **test-backed checklist**
demonstrating each is met:

| # | Acceptance criterion (OpenSpec) | Demonstrated by |
|---|---|---|
| C1 | New char spawns at Keep → equips at provisioner → hires henchman → travels to Caves → clears a tribe quest → returns and turns it in | M9 vertical-slice integration test (`tests/zones/test_m9_vertical_slice`) |
| C2 | Faction state transitions triggered by scripted player actions and observed in NPC behavior | `tests/faction` + the M9 standing-shift test (M4 ↔ M9) |
| C3 | Tribe-scoped repop halts and rival-tribe expansion both fire under test | `tests/repop` + world-build §13.5 leadership-halt-with-real-scouts (`tests/world_build/test_orchestrator`) |
| C4 | Disguised-Priest rotation differs in identity and clues across two simulated resets | `tests/disguised_priest` two-season-rotation scenario |
| C5 | Henchmen hire / follow / fight / take treasure share / refuse below morale | `tests/henchmen` |
| C6 | Default death (XP loss + retrievable corpse); hardcore death (delete + leaderboard) | `tests/death` |
| C7 | Season reset clears world state but preserves character data | `tests/seasonal_reset` + world-build §13.9 rebuild persistence |
| C8 | 50 concurrent players, <100 ms command latency | the M16 C8 latency test (§2) |

### 4.1 How the checklist is enforced as a test

The checklist is not prose alone — `tests/acceptance/test_criteria_coverage.py`
encodes the mapping as data (criterion id → the test node id(s) that prove it) and
asserts, for each criterion, that **the named test module/node exists and is
collected** (e.g. via `pytest`'s collection API or an import + attribute check).
This converts "all acceptance criteria demonstrably met" from a claim into a
machine-checked invariant: if a referenced proof test is renamed away or deleted,
the coverage test fails, flagging that a criterion lost its proof. C8 is proven by
the M16 latency test in the same suite; the other seven are proven by their
existing subsystem suites, which the coverage test **references but does not
re-run or duplicate** (no behavior is re-implemented here).

The coverage test's data table is the single authoritative list of "what 'done'
means for v1 acceptance," kept in one place for review.

---

## 5. Honesty and limitations (recorded, not hidden)

Each measurement states what it is and is not, in the test docstring and the
coverage checklist:

- **C8 latency** is single-process, server-side, per-command latency against a
  fully-populated `build_all()` world via the in-process transport (ADR 0005); it
  is **not** a wire-level measurement over 50 simultaneous sockets. The telnet
  fallback for that is documented in ADR 0005 and deferred.
- **Economy pacing** is a deterministic projection over representative wired-content
  values reaching the target band; it is **not** a completed 6-week live
  playthrough. Its assumptions are the named arc constants in `pacing.py`.
- **Criteria coverage** asserts the proof tests exist and are collected; C1–C7 are
  proven by their own subsystem suites (which M16 does not modify), C8 by the M16
  latency test.

This mirrors the world-build spec's "report, not silently cap" discipline (§11):
the value of the acceptance milestone is that the numbers are **honest and
reproducible**, not that they are flattering.

---

## 6. Testable contract (→ `tests/acceptance/`)

1. **C8 latency** (`test_latency_50.py`, engine): `run_load(50)` returns a report
   with `recall_built is True`, `driven_sessions == 50`,
   `commands_run == 50 * len(mix)`, and `latency.p95_ms < P95_BUDGET_MS` and
   `latency.max_ms < MAX_BUDGET_MS` (budgets named constants, under the 100 ms
   criterion with margin; §2.4). The world the load runs against is populated
   (asserted via positive mob/room presence).
2. **XP pacing** (`test_xp_pacing.py`, pure / Django-free): `project_arc` for the
   representative class over the modeled 6-week arc yields a final level in the
   target band (e.g. L9–L10); the projection is deterministic (same inputs → same
   result); `secure_xp` and `level_for_xp` are used unchanged (the model composes
   the existing cores, it does not re-derive them). A second case pins the per-week
   XP curve so a pacing-knob regression is caught.
3. **Pacing knobs are the single config** (`test_xp_pacing.py`): the projection's
   tunable inputs come from `world/rules/economy.py` + `world/rules/pacing.py`
   constants only; the OSE `progression._XP_TABLE` is untouched (asserted by
   referencing the canonical thresholds, not redefining them).
4. **Criteria coverage** (`test_criteria_coverage.py`): for each of the eight
   criteria C1–C8, the mapped proof test node(s) exist and are collectable; the
   table covers all eight (no criterion unmapped); a missing/renamed proof test
   fails the coverage test.

Behaviors 2–3 run Django-free (pure projection over the rules core); 1 uses the
Evennia test harness (architecture §6). The suite is organized as
`test_latency_50.py` (engine), `test_xp_pacing.py` (pure), and
`test_criteria_coverage.py` (collection-level).

---

## 7. Build slices (post-review)

After the M16 spec-review gate, the implementation is broken into loop-grabbable
slices, spec→test→impl each, in dependency order:

1. **XP-pacing projection** — `world/rules/pacing.py` (pure projection model +
   named arc/target constants) and `tests/acceptance/test_xp_pacing.py`; tune the
   economy/pacing knobs to land the target band and pin the curve. Pure, no boot.
2. **C8 latency measurement** — `tests/acceptance/test_latency_50.py` driving
   `loadharness.run_load(50)`; record the baseline, set the named budget under
   100 ms with margin, assert honesty + latency. Escalate (not weaken) if the
   observed p95 exceeds the criterion.
3. **Criteria-coverage checklist** — `tests/acceptance/test_criteria_coverage.py`
   encoding the §4 table and asserting every proof test is collectable; this is the
   capstone that declares v1 acceptance demonstrably met.

Each slice is one focused spec→test→impl session; none introduces new content or
reopens a locked decision.

---

## 8. Cross-references

- The runnable, populated target + the load harness this consumes: world-build
  spec (`world-build.md`) §11; `world.build.loadharness`; ADR 0005 (transport).
- The money/XP-on-secure math and the pacing knobs: economy spec (`economy.md`)
  §6–§7; `world/rules/economy.py`.
- XP thresholds + level lookup (unmodified OSE canon): `world/rules/progression.py`;
  CLAUDE.md §2 (level range 1–10, 6-week seasons).
- The eight acceptance criteria and their milestone mapping:
  `keep-on-borderlands-openspec-prompt.md` §"Acceptance criteria"; build-plan
  coverage map (`docs/build-plan.md`).
- Season-reset persistence boundary (C7): seasonal-reset spec; world-build §13.9.

---

## 9. Open decisions

None blocking. Two values are deliberately deferred to the slice that sets them
(not escalations — they do not reopen a locked decision):

- The exact `P95_BUDGET_MS` / `MAX_BUDGET_MS` figures — set in slice 2 from the
  observed baseline, under the 100 ms criterion with margin (§2.4).
- The exact play-arc constants and target band in `pacing.py` (encounters/week,
  average secured gp + kill XP per clear, target level band) — set in slice 1 from
  the representative values of the M9–M13 wired content, and reviewable as the named
  assumptions of the projection (§3.2–§3.3).

If a slice uncovers a genuine contradiction with a locked decision or an
unspecified behavior — for example, the observed 50-session p95 exceeding 100 ms
(criterion unmet), or no pacing-knob setting landing the target band without
distorting the economy — escalate via `docs/questions.md` rather than weakening a
test or inventing a requirement (PROMPT.md, CLAUDE.md §3).
