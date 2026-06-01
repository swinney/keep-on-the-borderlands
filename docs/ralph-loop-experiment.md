# The Ralph Loop Experiment — A Field Log

> A running, candid record of building **Keep on the Borderlands** (an Evennia
> MUD) with a [Ralph Loop](https://ghuntley.com/ralph/): Claude Code run
> unattended against a stable prompt and a living task list. Written as source
> material for a team presentation — successes, failures, and the decisions that
> mattered. **Living document**: appended at each milestone.

---

## TL;DR (the exec slide)

- **A Ralph Loop is a builder, not an architect.** It converges only as well as
  the scaffolding around it — specs, tests, hard gates, and stop conditions.
- **Quality comes from the gates, not the model.** Strict `ruff`/`mypy`/`pytest`
  + CI is what makes it safe to run a *cheaper* model unattended. We ran most
  work on Sonnet and reserved Opus for the genuinely hard turns.
- **"Progress = a commit, nothing else counts."** Every recovery, stall-detector,
  and review decision anchors on the commit graph, because a commit is the only
  proof a turn did real, gated work.
- **The failures were operational, not logical.** The loop wrote correct OSE
  rules and Evennia typeclasses; what bit us was a hung process, a gate that
  didn't mirror CI, a whitespace stop-signal, an off-task excursion, and — in
  M3 — a debugging spiral that tripped the stall-detector exactly as designed.
- **The stall-detector earned its keep in M3.** Two consecutive 20-minute
  timeouts on one hard task triggered the self-halt; a human escalated that turn
  to the stronger model and finished it in minutes. The model-by-risk strategy
  is not theory — it's the documented recovery path.
- **As of this writing:** 93 commits, 31 unattended loop turns, 284 passing
  tests, through M6 — the **entire systems layer is complete** (factions,
  henchmen, repop, seasonal reset). Zero red commits reached `main`. M4/M5 ran
  unattended on Sonnet; M6 ran unattended on Opus (stateful) with zero stalls.

---

## 1. The premise

Build an open-source persistent multiplayer MUD adapting module *B2: The Keep on
the Borderlands* (1979) on the [Evennia](https://www.evennia.com/) framework,
using Old School Essentials (B/X) rules — and build it **with a Ralph Loop**, to
learn where unattended agentic construction actually works and where it breaks.

The bet: if the *specs and tests* are good enough, an agent can grind through
implementation unattended, and the interesting engineering moves up a level — to
designing the harness that keeps the loop honest.

---

## 2. The setup that made it work

Decisions made *before* the loop ran a single turn — each chosen specifically to
help a loop converge:

| Decision | Why it matters to a *loop* |
|---|---|
| **Spec → test → implement, enforced** | No task starts without a spec + test scaffold. The test is the loop's definition of "done"; the spec is the contract it can't silently drift from. |
| **Pure rules core** (`world/rules/`, no Evennia) | The most bug-prone logic (OSE math) is unit-tested without booting Django — fast, deterministic, `mypy --strict`. |
| **Value-driven seam** | Combat *resolution* takes already-rolled values (`attack_hits(d20=20, …)`) instead of rolling internally. Every edge case (nat-20/nat-1) is deterministically testable, and the rules↔engine wiring stays *auditable*. |
| **Hard gates mirrored in CI** | `ruff format → ruff check → mypy --strict → pytest`. The loop physically cannot commit red; CI catches anything its self-gate misses. |
| **Lean, always-loaded `CLAUDE.md`** | Trimmed 732 → 184 lines. It's re-read every loop iteration, so every token is paid hundreds of times. Depth moved to on-demand docs. |
| **Container sandbox** (rootless Podman) | The loop runs `claude --dangerously-skip-permissions`; the container bounds the blast radius. |
| **Milestone gates** | A sentinel task between milestones makes the loop *stop itself* for human review at semantic boundaries. |

---

## 3. Lifecycle timeline

### Phase 0 — Specification generation (≈15 commits)
Drove OpenSpec to produce 11 deliverables: architecture overview, 9 subsystem
specs (each with testable scenarios + skipped pytest stubs), 5 zone outlines, a
quest catalog, a phased build plan, and a scaffolding plan. **The loop needs
something to converge against; this is it.** Open questions were resolved with
reasoning (license=MIT, 6-week seasons, ascending AC, …).

### Context refactor — lean cold-start contract
Trimmed `CLAUDE.md` from 732 → 184 lines, relocating strategy/rationale into
on-demand docs. Rationale: an always-loaded file is paid per *iteration*, so for
a long unattended run a 548-line trim is 548 lines × every turn.

### Phase 1 / M0 — Bootstrap (human-run, pre-loop)
`evennia --init mudgame` (Evennia 6.0 / Django 6.0 / Twisted 24.11), pinned deps,
documented the per-milestone settings plan, generated the root `tasks.md` from
the build plan, and built the loop runner + container. Deliberately *did not*
expand mypy scope or restore the Evennia override yet — doing so before
first-party code exists would break CI two different ways (a handoff note in
`tasks.md` flagged exactly when to do each).

### M1 — Rules core (pure OSE math)
`dice`, `abilities`, `progression`, `combat`, `saves`. Seeded the first three
modules **manually** (to validate the per-task shape and harden the gates), then
**handed off to the loop on Sonnet** for the rest. The loop fetched the OSE SRD
tables over the web to verify save/XP data rather than trusting memory. M1 ended
with 121 passing tests, all pure, no Django.

### M2 — Combat on the engine (complete)
The first Evennia/Django integration. **Turn 1 supervised on Opus** (the
config-critical `pytest-django` + `DJANGO_SETTINGS_MODULE` + mypy-override wiring,
where a slip breaks all downstream tests). Then **Sonnet** for the mechanical
remainder: `Character`/`Mob` typeclasses on the `traits` contrib, ticker-driven
combat rounds, the `attack` command, Vancian spells (`cast`/`rest`), and the
0-HP death-handoff stub. Shipped as **PR #1** — the first milestone routed
through the new branch → CI → Copilot-review flow (see §5.9).

### M2 review — the Copilot-PR trial (§5.9)
Copilot's review of PR #1 returned ~13 legitimate findings, several
independently re-deriving this project's own principles. The fixes landed on
the branch before merge. Disruption (a spec'd behavior that was non-functional
dead code) was **deliberately deferred** with an honest stub + a task, as it
needs combat-round declare/resolve timing beyond M2's scope.

### Loop observability — strengthening the human↔loop channel
Between M2 and M3 we hardened the status reporting the supervising session reads:
line-buffered live logs (`tail -f` shows progress, not just end-of-turn), a
`current.json` heartbeat (the turn running *now*), a git-derived `status.jsonl`
feed (one objective record per completed turn — task, model, exit code, commit),
and a `make status` digest. Shipped as **PR #2** (Copilot: 0 findings, clean).
This is what made the M3 stall *legible* — we could see "turn 13 exit 124, no
commit" without attaching to the container.

### M3 — Death & hardcore (complete; loop stalled, human-recovered)
Corpse creation, default death (XP loss + recall), hardcore permadeath +
leaderboard, and the irrevocable `[HC]` flag/marker. The loop cleared tasks 1–2
cleanly on Sonnet — then **stalled hard on task 3** (§5.10): two consecutive
20-minute timeouts, the self-halt fired, and the task was **finished manually on
Opus**. Tasks were completed test-first per the discipline; `tests/death` ended
fully green (11/11, no skips). The episode also surfaced a config-boundary bug
(§5.11): the loop had been adding `Co-Authored-By` trailers because the container
never sees the *host-global* `CLAUDE.md` where that rule lived. Shipped as
**PR #3**.

### M3 review — Copilot catches a real bug green tests missed (§5.9 cont.)
PR #3's review (9 findings, zero noise) flagged a genuine defect that all 11
green death tests had hidden: the death code treated `db.char_class` as a
`CharacterClass` enum, but the codebase convention (`commands/spells.py`) stores
it as a **string** — so both death paths would crash for any real character. The
tests passed only because they stored the *enum*, not the string the game
actually uses. This is the M3 analogue of M2's dice-seam finding: **an
independent reviewer with no shared assumptions catches the wiring bug; the
fix makes the tests exercise the real path.** Now true on every code PR.

### M4 — Faction state machine (complete; clean unattended run on Sonnet)
The **counter-example to M3**: same harness, same model, opposite outcome. The
loop ran all five M4 tasks (tribe/pair-state config, the `faction_manager`
GlobalScript, event deltas + decay, NPC aggression + `consider`, and the
shared-enemy thaw arithmetic) **start-to-finish on Sonnet with zero
intervention**, then **self-halted at the M4→M5 gate** exactly as the sentinel
specifies. Both new `PROMPT.md` guards held on every commit (no `Co-Authored-By`,
no stray debug scaffolding). `tests/faction` ended green (14 tests; 242 total).
**The lesson made concrete:** match model tier to task *type*, not size — M4 is
pure-ish logic against a detailed spec (the loop's sweet spot), whereas M3's
stall was stateful object-lifecycle work where a wrong mental model compounds.

### M5 — Henchmen (complete; second clean unattended Sonnet run)
Tavern hire flow (reaction roll, CHA-table cap, cost), follow/order commands +
combat AI, OSE loyalty/morale (flee/refuse thresholds), and XP/treasure share +
permadeath/re-hire. Notably, the task we expected to be risky — **follow/order
commands + combat AI**, the stateful/engine-coupled kind that stalled M3 — ran
clean on Sonnet under closer supervision. M5 completed all four tasks unattended
and self-halted at its gate; `tests/henchmen` green. Two clean unattended
milestones in a row (M4, M5) is the loop hitting its stride on well-specified
work. Batched with M6 into a single PR (see §10).

### M6 — Repop + seasonal reset (complete; Opus-from-start, zero stalls) + the batching dividend
The first milestone launched on **Opus from turn 1**, deliberately, because it
is *stateful* (repop Scripts, timers, leadership-halt, season_manager reset
orchestration) — the M3-stall category. It ran all six tasks unattended with
**zero timeouts**, validating "Opus-from-start on stateful work." M5+M6 were
**batched into one PR (#5)** to cut gate latency — and batching paid an
unexpected dividend: Copilot's review caught a **cross-milestone integration
bug that per-milestone review would have missed**. M3 had built a placeholder
leaderboard; M6 built the real season-aware one; nothing wired *death* to the
*season* leaderboard, so `fell` entries were unreachable via `per_season`
(death.md §4 behavior 10 unmet end-to-end). Each milestone's tests passed in
isolation; only seeing M3's and M6's code in *one* review surfaced the gap. Fix:
unify onto the single season-owned store (death → `season_manager.record_fell`),
delete the legacy placeholder. **Lesson: batching isn't only a latency win — it
widens the review's blast radius enough to catch integration drift that isolated
green suites never will.**

---

## 4. What worked (successes)

- **Spec-driven convergence is real.** With specs + skipped test stubs already in
  place, most turns were "unskip → implement → green," and the loop produced
  spec-faithful code: the morale check (`2d6 ≤ score`) had the direction right;
  the SRD save/XP tables matched the book; demi-human level caps were honored.
- **The cheaper model held.** The bulk of M1 and M2 ran on Sonnet and passed the
  same strict gates. The structure, not the model tier, carried the quality.
- **The loop used its environment well where it had it:** Evennia *contribs*
  (`traits`, `lazy_property`) per the architecture mandate; web research for
  authoritative data; TDD on every turn; even multi-agent workflows internally.
- **Zero red commits reached `main`.** Every push was CI-green across container,
  host, *and* CI environments.
- **Recovery was always safe.** Because the loop commits only on a green, clean
  tree, a killed/hung turn leaves nothing partial — kill-and-relaunch just retries
  the task.

---

## 5. What broke (the war stories)

The instructive part. None of these were the model "being dumb" — they were
scaffolding gaps.

### 5.1 The gate that didn't mirror CI  ·  *caught by supervising turn 1*
The first supervised turn produced code that passed `ruff check`, `mypy`, and
`pytest` — but **failed `ruff format --check`**, because `PROMPT.md`'s gate list
said "ruff check" and omitted the formatter, while CI runs `ruff format --check`
*first*. A correctly-typed, passing-tests commit would have gone CI-red.
**Fix:** the loop's self-gate must mirror CI *exactly*, in order. **Lesson:**
supervise turn 1 after any change — it pays for itself immediately.
→ commit `9746da6`

### 5.2 The logging that wasn't  ·  *expectation gap*
The first supervised turn produced **no log file** — per-turn logging lived only
inside the loop body, and the single-turn path bypassed it. **Fix:** unify both
modes through one logged `run_turn`. **Lesson:** instrument the thing you'll use
to review an unattended run *before* you run it unattended.
→ commit `701350e`

### 5.3 The hung container  ·  *the classic*
A turn's `claude -p` stalled — 8 minutes, ~0 CPU, no child processes, clean
working tree. Not a crash; a hang at the start of a turn (blocked on the API).
**Diagnosis playbook:** is the container up (`podman ps`)? is it *progressing*
(`git status` shows edits? `git log` shows commits? does `podman top` CPU-time
climb)? Flat CPU + clean tree + empty log = hung. **Recovery:** `podman stop`,
verify the last commit is intact and green, relaunch (which retries the task).

### 5.4 Hardening recovery so we stop babysitting
Rather than watch for hangs, we made the loop *self-recover*: wrap each turn in
`timeout` (kill a hung turn), **auto-retry** the next iteration (transient hangs
self-heal), and **stop after N consecutive no-commit turns** (escalate persistent
failure instead of spinning). **Lesson:** "progress = a commit" — the stall
detector watches `git HEAD`, not logs or exit codes, because only a commit proves
real work happened. → commit `0770a06`

### 5.5 The whitespace stop-signal  ·  *a one-character footgun*
The loop halted mid-M2 because a turn wrote *whitespace* to `STATUS.md`, and the
stop check (`[ -s ]`, "file is non-empty") treats any non-zero file as a stop
signal. **Lesson:** a stop-signal "mailbox" must distinguish *whitespace* from
*intent* — check for non-whitespace content, not file size. **Fixed:** `ralph.sh`
now stops only on non-whitespace content (`grep -q '[^[:space:]]'`).

### 5.6 The off-task excursion  ·  *the loop is a bare Claude install*
One turn ignored the next `tasks.md` task and instead spent itself "saving memory
about the project" — into the *container's* local home, which doesn't even persist
to host sessions. **Lesson:** the loop's container is a near-vanilla environment
— it had the account's claude.ai integrations (Gmail/Calendar/Drive) but **none
of the dev MCP it needed** (no Context7), and no project memory. Capability and
discipline must be *provisioned*, not assumed. **Fixed:** tightened `PROMPT.md`
(do only the `tasks.md` task; never write a blank `STATUS.md`; don't spin up
workflows for routine modules), and wired Context7 (§5.7).

### 5.7 No live framework docs  ·  *the standing gap*
With no MCP configured, the loop implements **Evennia 6.0 from training
knowledge, not current docs** — risky for a recent framework, and counter to our
own "always pull current docs for external libraries" rule. **Fixed:** a project
`.mcp.json` wires Context7 (verified `context7 ✓ Connected` in-container).
*Caveat:* availability ≠ use — the loop didn't always reach for it even once
configured; a `PROMPT.md` nudge may be needed.

### 5.8 Operational ceiling
Launching the loop as a tracked background process from an interactive session is
capped (10-minute tool limit). **The durable way to run a long loop is the
canonical one: `make loop` in your own tmux.** Interactive sessions are best for
*supervised* turns and the milestone-gate mechanics.

### 5.9 The Copilot-review trial  ·  *an independent reviewer re-derives your principles*
PR #1 (the M2 milestone) was the first run through the branch → CI →
Copilot-review flow. Copilot returned ~13 legitimate findings with near-zero
noise — and, with **no access to the ADRs**, it independently flagged the two
things this project is built on: the **dice-seam bypass** (engine code rolling
`randint` directly instead of via `world.rules.dice`, in four places) and the
**single-source-of-truth AC duplication** (`Mob.computed_ac` re-implementing the
formula). It also caught a *non-functional spec'd behavior* (spell disruption was
dead code) that all 211 passing tests missed — because the tests covered the
pieces, not the integration path. **Lesson:** green gates prove "runs and types";
an independent review catches "wired correctly." Different failure classes,
different tools. One finding (a claimed CI-failing lint) was **wrong** — verified
against a green CI — a reminder to check external feedback, not blindly apply it.

### 5.10 The debugging spiral  ·  *the stall-detector's first real save*
M3 task 3 (hardcore death) was the first task to **defeat the loop**. Two
consecutive turns hit the 20-minute timeout with no commit, so the
consecutive-no-progress detector (§5.4) self-halted and wrote `STATUS.md` —
working exactly as designed. The post-mortem was the interesting part: there
were **two nested bugs**. (1) A *real* Evennia object-lifecycle bug — hardcore
death deletes the character while its gear still names that character as its
`home`; Evennia dereferences `home` during teleport/`delete`, so the move
silently failed and cleanup raised `ObjectDoesNotExist`. (2) The model's own
**debug instrumentation became a second bug**: an `import sys` placed *inside* a
`for`-loop that didn't execute for empty corpses produced an `UnboundLocalError`,
whose symptoms it then misattributed to bug (1). It burned both turns chasing its
own scaffolding. **Recovery:** a human escalated the turn to **Opus**, which
separated the two failures, fixed the lifecycle bug by re-homing corpse contents
to a live object, deleted the debug cruft, and finished test-first in minutes.
**Lessons:** (a) the stall ceiling is what turns "infinite spin" into "bounded
cost + escalate" — it paid for itself here; (b) **model-by-risk is a recovery
mechanism, not just a launch setting** — the documented move when a cheap model
stalls on a stateful task is to escalate, not to keep retrying; (c) debug
scaffolding must never survive a turn — a `PROMPT.md` guard ("remove diagnostic
prints before committing") is the standing fix.

### 5.11 The rule the loop couldn't see  ·  *config-boundary blindness*
Every loop commit carried a `Co-Authored-By: Claude` trailer — violating a
standing owner rule. The cause was structural, not disobedience: the rule lived
in the **host-global** `~/.claude/CLAUDE.md`, but the container mounts only the
*project* tree and a throwaway claude-home, so the loop's Claude never saw it.
**Lesson:** an unattended loop obeys only the constraints present *in its
sandbox*. Anything in your personal/global config is invisible to it — encode
project-binding rules in the repo (`PROMPT.md` / project `CLAUDE.md`), not in
your host environment. **Fixed:** the no-`Co-Authored-By` rule is now in
`PROMPT.md`; the first commit after the fix was clean.

---

## 6. Architectural decisions worth presenting

Recorded as ADRs in `docs/decisions/`:
- **0001 — Podman (rootless)** to bound `--dangerously-skip-permissions`.
- **0002 — Pro/Max auth** persisted into the container.
- **0003 — uv** for the host Python environment.
- **0004 — Source layout & tooling boundary:** first-party code lives under
  `mudgame/` (Evennia's import path); `ruff` lints *our* code but excludes
  Evennia's generated plumbing; `mypy --strict` applies only to the *pure*
  Evennia-free modules, because strict-typing untyped framework base classes is
  intractable. This boundary is what lets the gates be strict *and* green.

Plus the cross-cutting ones above: the pure rules core, the value-driven seam,
the lean context file, the model strategy, and the milestone-gate sentinel.

---

## 7. Patterns worth stealing (the memorable slides)

1. **The gate is the safety net, not the model.** Make errors cheap to catch and
   impossible to commit; then a cheaper model is safe to run unattended.
2. **Progress = a commit.** Anchor recovery and stall-detection to the commit
   graph, not logs or exit codes.
3. **Milestone-gate sentinels.** Drop a task that says "when milestone N is done,
   write a reason to the stop-mailbox and halt." The loop pauses *itself* at a
   semantic boundary — deterministic review, no racing to kill a process.
4. **Supervise turn 1** after any model switch or milestone jump. One turn is the
   cheapest possible integration test of the loop itself.
5. **Model by risk:** cheap model for mechanical/well-specified work; expensive
   model for config-critical and stateful turns. Set it *explicitly* per launch —
   no "auto" routing.
6. **Provision the loop's environment.** It's a bare Claude install; give it the
   MCP/docs/constraints it needs rather than expecting your rich session's tools.
7. **Two-tier context.** Always-loaded files stay minimal (paid per iteration);
   depth goes in on-demand docs (cached, read only when needed).

---

## 8. Metrics (as of this writing)

| Metric | Value |
|---|---|
| Total commits | 93 |
| Unattended loop turns | 31 |
| Models used | Sonnet 4.6 (M1/M2/M4/M5) · Opus 4.8 (config-critical turns, M2-turn-1 supervise, M3 stall recovery, **all of M6** stateful) |
| Tests | 284 passing / 40 Phase-0 stubs skipped |
| Pure rules / logic modules | 8 (`dice`, `abilities`, `progression`, `combat`, `saves`, `spells`, `factions`, `henchmen`) + system packages (`repop`, `season`) |
| Red commits reaching `main` | 0 |
| Milestones complete | Phase 0, M0–M6 (**entire systems layer**) |
| Loop tasks needing human recovery | 1 (M3 task 3 — debugging spiral, §5.10) |
| Milestones run fully unattended | 3 (M4, M5 on Sonnet; M6 on Opus — all self-halted at gates) |
| Copilot-reviewed PRs | #1 (~13) · #2 (clean) · #3 (9, 1 real bug) · #4 (5, 2 real bugs) · #5 (1, a cross-milestone integration bug) |

---

## 9. Honest open challenges

*Resolved during the M2 review (§5.5–5.7): whitespace stop signal, on-task
`PROMPT.md` guards, and Context7 wiring are all done.* Still open:

- **Get the loop to actually use Context7** — wiring it in wasn't enough; it
  didn't reach for it unprompted (§5.7). Likely needs an explicit `PROMPT.md`
  instruction to consult live docs for Evennia APIs.
- **The rules↔engine wiring audit** must stay a *human/independent-review* check:
  gates prove code runs and types, not that the engine calls the right pure
  function. Copilot caught four `randint`-bypasses and the `Mob` AC duplication
  that all green tests missed (§5.9) — keep that review step.
- **Spell disruption** is deferred dead-code-stub pending combat-round
  declare/resolve timing (a tracked follow-up task).
- **Token efficiency:** the loop sometimes spins up a full multi-agent workflow
  for a trivial module — more cost than a single-agent turn needs.
- **Debug-scaffolding hygiene (§5.10):** a turn that adds diagnostic prints can
  trap itself; `PROMPT.md` should explicitly require removing them before commit,
  and stateful/object-lifecycle tasks may warrant launching on Opus from the
  start rather than stalling first.

---

## 10. Scaling the loop — where parallelism helps (and where it doesn't)

The instinct when asked to "go faster" is *more containers, more agents in
parallel*. For a convergence loop that's mostly **wrong** — and seeing why is
the interesting part.

**The loop is serial *within* a milestone, by design.** Convergence comes from
*one task → one commit → clean tree*. Every systems-layer task touches shared
files — `characters.py`, `npcs.py`, the `pyproject` mypy-scope line, the shared
test dirs. Two agents on the same milestone collide on those files; you'd trade
build time for merge-conflict time. **Don't parallelize the loop.**

**The architecture is parallel *across* content, also by design.** CLAUDE.md §3
mandates "modular zones, each its own package under `world/zones/` — the loop
works one zone without breaking another." That is a *parallelization charter*.
The systems layer (M4–M6: faction, henchmen, repop) is shared-state and stays
serial; the content layer (M7–M11: zones, tribes) is embarrassingly parallel.
**M10 is the extreme case — five tribes (orc/goblin/hobgoblin/bugbear/gnoll),
each an independent package → five containers at once.**

So velocity comes from four moves, not from cloning the loop:

1. **Batch clean milestones per PR.** The biggest *serial latency* is the
   human-gate cycle (PR → CI → review → fixes → merge), not the turns. Run
   several clean milestones on one branch, review once. (M5+M6 batched this way.)
2. **Auto-merge when the independent reviewer is clean.** CI green + zero Copilot
   findings → merge without a human round-trip. Stop for a human only when a
   finding needs judgment.
3. **Fan-out harness for the content layer.** From M7, give each container its
   own **git worktree** + its own **`.ralph/` state dir** (today the runner
   hard-codes one `/workspace/.ralph` with a single turn counter — two
   containers on one bind-mount corrupt each other's loop state and git index).
   Then run zones/tribes concurrently and merge as each lands.
4. **Match model tier to task *type*, from turn 1.** Opus-from-start on
   stateful/object-lifecycle milestones (M6's Scripts/timers/reset hooks) to
   avoid the stall-then-escalate waste (§5.10); Sonnet on pure-logic ones.

**The non-obvious lesson for the slide:** *you don't speed up a convergence loop
by parallelizing the loop — you parallelize the independent units the
architecture was designed to produce.* The work to make that possible was front-
loaded into the spec corpus and the modular-zone decision, long before a single
line of zone code existed.

---

## 11. How this log is maintained

A living document, updated by a human (or supervised) session **as work
progresses** — *not* by the unattended loop itself (see §5.6). Each milestone
appends: what shipped, what broke, and what we changed in the harness as a result.
