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
- **As of this writing:** through M9 — systems layer + the Keep, the wilderness,
  *and* the kobold-cave vertical slice that proves every subsystem composes
  end-to-end (spawn → travel three zones → clear a tribe on a bounty → bank for
  XP). 426 passing tests, zero red commits reached `main`. M4/M5 on Sonnet;
  M6/M7/M9 on Opus clean; M8 and M9 each survived an interruption (session-limit
  outage; host reboot) and recovered with zero lost work — the harness has now
  held three independent times.

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

### M7 — Keep zone (complete; first content milestone; the loop authored its own spec)
The systems→content boundary. The loop built the Keep's rooms/exits, the
provisioner economy + bank (XP-on-secure), tavern/chapel NPCs, and — the exit
criterion — a **full onboarding integration test: spawn → equip → hire → rest**,
the first time the systems run together as a playable flow (a direct precursor
to M9's vertical slice). Two process notes worth a slide: (1) **the loop wrote a
missing spec itself** — Phase 0 hadn't detailed the economy, so the loop spent
three turns spec → test-stubs → implementation (PROMPT workflow steps 3–5),
exactly as designed, which is why M7 ran longer than prior milestones; (2) run
on **Opus** (integration-heavy), it completed all four tasks with no stall.
351 tests green.

### M8 — Wilderness zone (complete; a stall + an outage, recovered with zero lost work)
The xyzgrid hex map, travel, encounter tables, and set-pieces. M8 stacked two
unrelated failures and is the cleanest "the harness held" story so far:
1. **A new dependency the loop's sandbox lacked.** xyzgrid needs SciPy — caught
   by a pre-launch import smoke test, fixed across *both* manifests (host
   `uv`/`pyproject` and the container's `pip` list) (§5.12).
2. **A real Sonnet timeout, then a session-limit outage.** The xyzgrid
   integration genuinely exceeded one 20-min Sonnet turn (the M3-style "stateful
   integration" stall); the escalation to Opus then bounced off an account
   session limit. **Nothing was lost:** turn 40's substantial WIP (a 192-line
   `xymap` + the package) lived in the bind-mounted tree, not the container, so
   when the limit reset, Opus finished it from the WIP in one pass. "Progress =
   a commit" means killed/limited turns cost only clock.
   *Diagnostic footnote:* a no-commit turn has multiple causes the stall-detector
   can't distinguish (timeout `exit 124` vs limit-bounce `exit 1`) — only the
   turn log tells them apart; read it before concluding *why*. And committing to
   the loop's branch *while it runs* perturbs the very `git HEAD` signal the
   stall-detector uses (a docs commit masked turn 40's stall once).
Copilot's PR #7 review was the lowest-severity yet — 5 findings, no real bugs (a
deferred stub exit, a missing idempotency test, two doc-accuracy fixes), plus one
**verified-false** mypy-exclude claim (falsified in seconds by injecting a type
error and watching `mypy` stay green). 371 tests green.

### M9 — Kobold cave vertical slice ⭐ (the critical-integration milestone; a third "harness held")
The milestone the whole build order points at: the first cave, but really a
proof that *every subsystem composes*. Five tasks, all on Opus-from-start (the
model-by-risk call for an integration milestone), all clean — caves rooms+mobs,
the chief+shaman leadership-halt wiring into M6, the M4↔M9 faction-standing tie,
the Guildmaster bounty + treasure→XP-on-secure loop, and the headline exit test.
That last test (`test_m9_vertical_slice`) drives one live world with all three
zones built and linked through the full acceptance loop — spawn → equip → hire →
travel the real keep↔wilderness↔caves exit graph → clear the tribe → return →
turn in → bank for XP — so a break in any inter-zone link surfaces *here*, before
M10 builds seven more caves the same way. It also pins the cross-subsystem kill
credit (a henchman's kills credit its employer's bounty *and* faction standing,
henchmen.md §4) and the XP-on-secure idempotency (the same coin never pays twice).

The war story is a **third independent "the harness held"** (after M3 and M8),
this time from the most mundane cause yet: a **host reboot**. Turn 50 had written
the 272-line integration test and it *passed* — but the reboot killed the turn
seconds before its `git commit`. Because the test lived in the bind-mounted tree,
not container-ephemeral state, the work survived verbatim; the recovery was to
re-run it (green), run the full gate, and commit the loop's own completed work.
*Lesson reinforced:* the commit boundary is the durability guarantee, but it is
not the only state worth inspecting — checking the actual working tree turned a
presumed "redo task 5" into a one-command "just commit it," saving a full Opus
turn. Verify real state; don't trust the checkbox alone. 426 tests green.

### M10 — Remaining caves (the fan-out experiment, and why we retired it)
M10 is the milestone §10 flagged as "the extreme parallel case" — five
independent tribes — so we built the **fan-out harness** (one clone + container
per tribe, pooled, Sonnet, per-tribe PRs) and launched all five. It *worked* in
the narrow sense: five green tribes merged. But the honest verdict, reached the
same session, is that **at this scale the fan-out was net-negative, and we
retired it.** Four reasons, each its own war story (§5.13–5.16):

1. **Intent isolation ≠ process isolation (§5.13).** Each tribe had its own
   clone, branch, and scoped `tribe-tasks.md` — perfect *infrastructure*
   isolation — but nothing stopped a loop from reading the canonical `tasks.md`
   and over-delivering. The orc loop built the *entire milestone* before we
   stopped it. Scope was enforced in the filesystem, not the prompt.
2. **A discovery aggregator silently re-shares "isolated" files.** The per-tribe
   subpackage design promised zero shared-file edits, but `test_caves.py` asserts
   against the *aggregate* namespace — so the moment a second tribe added a
   chief/shaman, the kobold leader-lookup turned ambiguous and *every* tribe loop
   independently edited the same helper. *A test of the aggregate is an implicit
   shared file; it belongs with the hub, not edited per unit.*
3. **"All PRs green" ≠ "main green."** Each tribe PR's CI proved only kobold +
   that tribe; the six-tribe union was a global property no single PR verified —
   and the merged-union check is exactly where a real isolation leak surfaced
   (Copilot caught it: a teardown that leaked mobs across parametrized cases).
   The merged-main verification is mandatory, not optional.
4. **Coordination cost swamped the parallelism.** Per-tribe PRs, a manual Copilot
   request on each, clone/container juggling, and a *fail-open* auto-merge gate
   (the lander matched the wrong Copilot bot login and would have merged
   unreviewed PRs) — all human-supervised. For five small packages that each take
   one focused turn, the overhead exceeded the wall-clock saved.

**The salvage saved it.** Because the rogue orc branch was complete *and green*,
recovery was to cherry-pick each clean per-tribe subpackage from it onto fresh
branches off `main` and land them serially through review — the runaway became
the asset. The minotaur maze + Shrine passage and the cross-tribe
rivalry/repop-halt integration test (the M10 exit: *"faction rivalries and repop
halts demonstrably fire under test"*) came the same way. 576 tests green; caves
complete.

**Verdict: retired.** The content layer is parallel *in principle*, but at this
project's scale the serial single-loop build is simpler and the parallelism
wasn't worth its coordination tax. The harness scripts + this retrospective stay
as the record. *The deeper lesson outlived the harness: the bottleneck was never
turn throughput — it was the human-gate cycle and operator discipline, and more
containers fix neither.*

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

### 5.12 The dependency that wasn't there  ·  *host↔loop environment parity*
M8's wilderness spec mandates Evennia's `xyzgrid` contrib (coordinate hexes +
web-client map rendering, architecture §2). A **pre-launch smoke test** — just
importing `xyzgrid` before turning the loop loose — surfaced that it requires
**SciPy**, which wasn't installed. Turn 1 would have died on the import. Two
lessons, both about the gap between *your* environment and the *loop's*:
- **The host and the loop have separate dependency manifests that must move
  together.** The host resolves deps via `uv` (`pyproject` + `uv.lock`); the
  loop container installs via a **hard-coded `pip` list in the `Containerfile`**.
  Adding SciPy to only one would pass that environment's gate and fail the other
  — silent host↔loop↔CI drift. The fix was a *two-sided* edit (pyproject/uv.lock
  **and** Containerfile) + a container rebuild + a verify-in-container. Tellingly,
  the first rebuild *looked* successful but `import scipy` still failed in the
  container, because I'd updated only the host manifest — the smoke test caught
  that too. **"It works on the host" proves nothing about the container the loop
  actually runs in.**
- **Smoke-test a new capability before asking the loop to use it.** The import
  check cost seconds; discovering it via a stalled 20-minute turn (or the loop
  escalating to `questions.md`) would have cost far more. Verify the tool exists
  *before* the task depends on it.

This also met the locked "avoid third-party deps unless strictly necessary" rule
head-on: SciPy is heavy (NumPy, compiled wheels), so adding it was a **surfaced,
deliberate decision** (xyzgrid is the spec'd + architecturally-chosen mechanism
for the web-client map, a v1 default) — presented for sign-off, not slipped in.

---

### A different class of failure: operator discipline (the M10 session)

5.1–5.12 were *scaffolding gaps* — the model wrote good code; the harness around
it had holes. 5.13–5.16 are a different and more uncomfortable category: the
**operator** (the supervising agent driving the session) went off the rails while
the underlying methodology held. The system was sound; the hands on it were not.
Worth recording precisely because they're the failures a "the loop works!" story
usually omits.

### 5.13 The fan-out's intent-isolation gap  ·  *scope lived in the filesystem, not the prompt*
The fan-out gave each tribe its own clone, branch, and scoped `tribe-tasks.md` —
flawless *process* isolation. But a `claude -p` loop reads the whole repo, and
nothing forbade it from opening the canonical `tasks.md` and "helpfully" building
the next tribe too. The orc loop built **all six tribes + minotaur + the exit**
before we stopped it. **Lesson:** infrastructure isolation ≠ intent isolation; a
scoped task list is a hint, not a fence — the scope constraint has to be in the
prompt (and ideally enforced), not just the directory layout.

### 5.14 The flaky-test rabbit hole  ·  *brute force before analysis*
A `test_build_creates_every_room` failure seen **once** sent the operator into
~15+ full-suite reproductions chasing a "flaky" bug — before the near-free
analysis that should have come first: the zone builder is provably *per-room
idempotent* (it cannot under-create the room set), and the test DB is **in-memory**
(per-process, so concurrent runs can't corrupt it). The failure never reproduced
in a clean environment; the evidence pointed back at the operator's own concurrent
containers (§5.15). **Lesson:** for an intermittent failure, ask *is it possible
from the code? is it an infra artifact? does it matter?* **before** the
reproduction loop. One observed failure is not a deterministic bug. (Real
test-isolation debt does exist — Copilot later pinpointed a concrete leak in
seconds — which is the point: cheap analysis and review find these; brute force
burns hours.)

### 5.15 Self-inflicted environment chaos  ·  *background-process hygiene*
Chasing 5.14, the operator `&`-backgrounded `podman run` commands that detached
into **auto-named** containers (`boring_austin`, `quizzical_turing`). Every
cleanup grepped the `kotb-` name prefix, so they were invisible — they ran full
pytest suites on a loop for an hour, starved CPU, and made killed pytest appear to
"respawn" (a new container kept launching it). ~38 short-lived waiter tasks also
piled up. **Lessons:** never bare-`&` a long job — use a tracked background
mechanism that's killable by id; **name *and* verify** with a *broad* process
check, not a name-prefix grep that auto-named containers slip past; don't pipe a
backgrounded job through `tail` (it buffers — you fly blind); one orchestrator at
a time. (Captured as the `bg-process-hygiene` operator memory.)

### 5.16 The Copilot epistemic spiral  ·  *four wrong theories vs. one ground truth*
Asked why Copilot auto-review seemed to have stopped, the operator produced
**four** successive confident causal theories — "token permissions" → "never
automatic" → "auto but rate-limited" → "burst lag" — each inferred from PR
timestamps and a `gh api .../rulesets` call that returned `[]` (a *permissions*
artifact, not "no rulesets"), and each **contradicting the user**, who held ground
truth: they request Copilot manually; a ruleset on the default branch covers it.
**Lesson:** don't construct causal narratives for external-system behavior from
indirect signals; state what's verified, flag uncertainty, and defer to the user's
direct knowledge of their own setup. One verified fact beats a tidy story.
(Captured as the `defer-to-ground-truth` and `triage-before-brute-force`
operator memories.)

**The meta-lesson:** the Ralph methodology proved *resilient* this session — it
absorbed a reboot's worth of operator thrash without a red commit or lost work —
which is itself a finding, but a dangerous one: resilience masks sloppiness. The
portable framework needs an **operator-discipline checklist** (background-process
hygiene, triage-before-brute-force, defer-to-ground-truth) as a first-class
artifact alongside the loop mechanics.

---

### 5.17 The green gate over a hollow world  ·  *liveness ≠ readiness; the smoke test as independent verifier*
The `add-game-compose` change (containerize the game for Compose) was the first
built **not** via the loop but through OpenSpec `explore → propose → apply`, with
the operator in the loop interactively. The unit gate — `ruff` + `mypy --strict`
+ 830 tests — stayed **green the entire time** while the actual container was
broken three different ways. Only the **end-to-end smoke test** (a real `compose
up` against a throwaway volume, written straight from the spec's scenarios) found
them:
1. the image was missing `server/logs` — a runtime dir git doesn't track, so it
   never entered the build context — and Evennia couldn't initialise;
2. `evennia shell -c` (my chosen way to create the superuser + build) runs
   Evennia's **interactive onboarding prompt** before the snippet and doesn't
   reliably commit — so writes vanished and the container restart-looped;
3. `at_initial_setup` builds the world **for account #1**, so the superuser must
   exist *before* `evennia start`, or the world comes up empty.
Each "failure" first looked like a product bug and was in fact one — but the
telltale was that **a port answering is not the world being ready**: Evennia's
Portal binds telnet 4000 with no database, so every liveness check passed while
the Server/world was absent. The same liveness-vs-readiness gap then bit the test
harness itself (it read the room count before the async build finished).
**Lesson:** the unit test pyramid verifies the *parts*; only an integration test
that exercises the real artifact end-to-end verifies the *whole*. For a two-process
app, assert **readiness** (the built world, read from the persisted DB), never mere
**liveness** (a port). The smoke test is to deployment what Copilot (§5.9) is to
code review — an independent verifier operating at a level the author's own green
checks can't see.

**The debugging meta-lesson (a 5.16 echo, inverted):** resolving the three bugs
took several wrong theories — "the `EVENNIA_DATA_DIR` override isn't applied,"
"`evennia shell -c` doesn't commit" — and every time the move that actually worked
was to **stop theorising and inspect the container**: list the `*.db3` files,
count their tables and rows, dump the *full* boot log. §5.16 was about deferring to
the user's ground truth on an external system; this is the same discipline turned
on a system I *controlled* — the database file on the volume was the ground truth,
not my model of the entrypoint. (Reinforces `defer-to-ground-truth` and
`triage-before-brute-force`.)

**Two process notes worth a slide.** (a) The spec/design/ADR artifacts were
*refined mid-implementation* as ground truth corrected the plan (the abandoned
`evennia shell -c` build is recorded in design D3) — the `apply` workflow treats
that as normal, and it keeps the change record honest rather than aspirational.
(b) The CI "failure" was **not a test failure**: the suite legitimately grew to
~9.5 min and hit the job's 10-min cap, which surfaces as a red ✗ indistinguishable
from a real break — a silent-truncation cousin. Raising the cap was the fix; the
lesson is to *read the failure* (`830 passed … operation was canceled`) before
assuming the code broke. And Copilot again earned its seat: it caught the doc-rot
my mid-implementation redesign left behind (proposal/ADR/install guide still
describing the abandoned approach) — the "changed the code, not the story" class.

---

### 5.18 The player is the last verifier  ·  *830 green tests over an unplayable game*
Immediately after §5.17, the operator did the one thing no part of the harness
does: **played the game.** They created an account and found their character had
**no location at all** — `create`d players spawned nowhere and were unreachable
until a superuser teleported them. 830 passing tests, a green container smoke
(§5.17), and a clean Copilot pass had all signed off on a game you could not
actually start. The cause was textbook: `at_object_creation` never set a
location, and the project sets no `START_LOCATION`. The reason the suite missed it
is the sharpest part — the onboarding test *set `char.location` by hand* with the
comment "spawns at the recall point." It **simulated the spawn**, so it verified
everything *downstream* of placement (gold, shops, hire, rest) while never testing
placement itself. A green test that fakes the one precondition that matters is
worse than no test: it radiates false confidence. **Lesson:** automated coverage
verifies the parts you *thought* to check; a human exercising the real artifact
end-to-end is the only thing that surfaces the precondition you assumed. "All
tests green" and "the smoke test passed" do not imply "playable" — at some point a
person has to actually play it, and that session is itself a verification stage,
not a victory lap. (Copilot then caught the fix's over-reach — it would have
overridden an explicitly-passed `location` — narrowing it to "only fill an unset
location": the independent reviewer trimming the fix, exactly as in §5.9.)

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
| Total commits | 158 |
| Unattended loop turns | 50 (M1–M9, single loop) · M10 ran as the fan-out (5 tribe loops) then hands-on salvage + serial integration |
| Models used | Sonnet 4.6 (M1/M2/M4/M5; M8 content) · Opus 4.8 (config-critical turns, M2-turn-1, M3 recovery, all of M6/M7/M9, M8 xyzgrid recovery) |
| Tests | 576 passing / 40 Phase-0 stubs skipped |
| Pure rules / logic modules | 8 + system packages (`repop`, `season`, `quests`) + zones (`keep`, `wilderness` on xyzgrid, `caves`) |
| Red commits reaching `main` | 0 |
| Milestones complete | Phase 0, M0–M6 (systems) + M7 (Keep) + M8 (wilderness) + M9 (kobold vertical slice ⭐) + **M10 (all caves; fan-out tried then retired §3/§5.13–5.16)** |
| Loop tasks needing human recovery | 3 (M3 §5.10; M8 §5.12; M9 reboot) — zero lost work. M10 added heavy *operator* thrash (§5.13–5.16), also zero lost work: the methodology absorbed it |
| Specs the loop authored itself | 2 (M7 economy, M8 wilderness detail) |
| Copilot-reviewed PRs | #1 (~13) · #2 (clean) · #3 (9, 1 real bug) · #4 (5, 2 real bugs) · #5 (1, integration bug) · #6 (clean) · #7 (5) · #8 (1) · #9 (1, real UTC bug) · #10 (3) · #11 (clean) · #12 (3, dark-flag flavor) · #13 (1, dead test assertion) · #14 (2) · #15 (1, stale doc) · #16 (1, **real test-isolation leak**) — Copilot earned its keep on the M10 salvage |
| Fan-out experiment (M10) | 5 tribes built in parallel containers; **retired** — net-negative at this scale (§3 M10). Scripts kept as the experiment record |

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
serial; the content layer (M7–M11: zones, tribes) is parallel *in principle*.
**M10 was the extreme case — five tribes, five containers at once — and we
actually built and ran the fan-out harness for it. Verdict: net-negative at this
scale, retired** (see the M10 entry in §3 and §5.13–5.16). The parallelism worked
mechanically, but the coordination tax — scope drift, an aggregator that
re-shared a test file, per-tribe PRs + manual reviews, a fail-open merge gate —
exceeded the wall-clock saved for five packages that each take one focused turn.

So velocity comes from four moves, not from cloning the loop:

1. **Batch clean milestones per PR.** The biggest *serial latency* is the
   human-gate cycle (PR → CI → review → fixes → merge), not the turns. Run
   several clean milestones on one branch, review once. (M5+M6 batched this way.)
2. **Auto-merge when the independent reviewer is clean.** CI green + zero Copilot
   findings → merge without a human round-trip. Stop for a human only when a
   finding needs judgment.
3. **~~Fan-out harness for the content layer.~~ TRIED AT M10 → RETIRED.** The
   theory was sound (each container its own clone/worktree + its own `.ralph/`
   state dir; run zones/tribes concurrently; merge as each lands) and the harness
   *ran* — but the net was negative at this scale (§3 M10, §5.13–5.16). The
   serial single-loop build is simpler and the human-gate cycle, not turn
   throughput, was always the real bottleneck. Build content serially.
4. **Match model tier to task *type*, from turn 1.** Opus-from-start on
   stateful/object-lifecycle milestones (M6's Scripts/timers/reset hooks) to
   avoid the stall-then-escalate waste (§5.10); Sonnet on pure-logic ones.

**The non-obvious lesson for the slide:** *you don't speed up a convergence loop
by parallelizing the loop — you parallelize the independent units the
architecture was designed to produce.* The work to make that possible was front-
loaded into the spec corpus and the modular-zone decision, long before a single
line of zone code existed.

**Coda (M10):** we proved you *can* parallelize those units — and then learned
that *can* isn't *should*. At this project's scale the coordination tax of the
fan-out (§3 M10) outweighed the parallel execution; the three moves that actually
paid were the ones attacking *serial latency* — batch milestones, auto-merge on a
clean reviewer, match model to task type — not the parallel-execution one. Reach
for fan-out only when a single content unit is large enough that its build time
dominates the per-unit coordination cost; five one-turn packages are not that.

---

## 11. How this log is maintained

A living document, updated by a human (or supervised) session **as work
progresses** — *not* by the unattended loop itself (see §5.6). Each milestone
appends: what shipped, what broke, and what we changed in the harness as a result.
