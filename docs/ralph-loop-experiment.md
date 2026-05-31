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
  didn't mirror CI, a whitespace stop-signal, and an off-task excursion — all
  fixable with better scaffolding.
- **As of this writing:** 43 commits, 8 unattended loop turns, 156 passing tests,
  through M2 (combat on the engine). Zero red commits reached `main`.

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

### M2 — Combat on the engine (in progress)
The first Evennia/Django integration. **Turn 1 supervised on Opus** (the
config-critical `pytest-django` + `DJANGO_SETTINGS_MODULE` + mypy-override wiring,
where a slip breaks all downstream tests). Then **Sonnet** for the mechanical
remainder: `Character`/`Mob` typeclasses on the `traits` contrib, ticker-driven
combat rounds, the `attack` command. 156 passing tests at last green.

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
*intent* — check for non-whitespace content, not file size. *(Fix pending.)*

### 5.6 The off-task excursion  ·  *the loop is a bare Claude install*
One turn ignored the next `tasks.md` task and instead spent itself "saving memory
about the project" — into the *container's* local home, which doesn't even persist
to host sessions. **Lesson:** the loop's container has **no MCP, no skills, no
project memory** — it's a vanilla `claude login`, a *different* (poorer)
environment than an interactive session. Capability and discipline must be
*provisioned* (a project `.mcp.json`, a tighter `PROMPT.md`), not assumed.

### 5.7 No live framework docs  ·  *the standing gap*
With no MCP configured, the loop implements **Evennia 6.0 from training
knowledge, not current docs** — risky for a recent framework, and counter to our
own "always pull current docs for external libraries" rule. *(Fix planned: wire
Context7 into the container via `.mcp.json`.)*

### 5.8 Operational ceiling
Launching the loop as a tracked background process from an interactive session is
capped (10-minute tool limit). **The durable way to run a long loop is the
canonical one: `make loop` in your own tmux.** Interactive sessions are best for
*supervised* turns and the milestone-gate mechanics.

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
| Total commits | 43 |
| Unattended loop turns | 8 |
| Models used | Sonnet 4.6 (bulk) · Opus 4.8 (config-critical turns + reviews) |
| Tests | 156 passing / 103 Phase-0 stubs skipped |
| Pure rules modules | 5 (`dice`, `abilities`, `progression`, `combat`, `saves`) |
| Red commits reaching `main` | 0 |
| Milestones complete | Phase 0, M0, M1; M2 in progress |

---

## 9. Honest open challenges

- **Wire live framework docs** (Context7) into the loop so Evennia code isn't
  written from stale training knowledge.
- **Whitespace-robust stop signal** (§5.5).
- **Keep the loop on-task** — tighten `PROMPT.md` against excursions (§5.6).
- **The rules↔engine wiring audit** must stay a *human* check: gates prove code
  runs and types, not that the engine calls the right pure function. (We already
  caught one case where a typeclass re-implemented the AC formula inline instead
  of calling `world.rules.combat.armor_class`.)
- **Token efficiency:** the loop sometimes spins up a full multi-agent workflow
  for a trivial module — more cost than a single-agent turn needs.

---

## 10. How this log is maintained

A living document, updated by a human (or supervised) session at each milestone
gate — *not* by the unattended loop itself (see §5.6). Each milestone appends:
what shipped, what broke, and what we changed in the harness as a result.
