# Ralph Loop — First-Principles Evaluation (Exploration Backlog)

> Forward-looking companion to `ralph-loop-experiment.md`. Where the field log
> is a **retrospective** ("here's what happened at each milestone"), this doc is
> the **evaluation** ("which parts of the process actually earned their keep, and
> what is the portable framework underneath"). It exists to feed the project's
> stated end-deliverable: *distill a portable Ralph-loop framework — methodology
> vs. project-specific.*
>
> Format: a set of open **threads** to pull in explore sessions. Each is a
> question, why it matters, and its status. Pull one at a time; record findings
> inline so the next session inherits them.

---

## The central tension (the frame for everything below)

The documents describe one thing; current practice is another.

```
  DOCUMENTED HARNESS                     ACTUAL PRACTICE (current mode)
  ralph-loop.md / PROMPT.md              ralph-loop-driving (memory)
  ┌──────────────────────────┐          ┌──────────────────────────┐
  │ while true;              │          │ supervised-direct serial  │
  │   claude -p < PROMPT.md  │  ──vs──  │ building: supervising      │
  │ done  (unattended,       │          │ session edits the tree     │
  │ Podman, --dsp, stall-    │          │ directly, one commit/slice │
  │ detector, fan-out)       │          │ container loop = aspirational│
  └──────────────────────────┘          └──────────────────────────┘
```

By M11 we had **stopped running a Ralph Loop** in the literal (unattended) sense
and were running a disciplined supervised build that *inherited the loop's
scaffolding*. Naming hides which half delivered: the literature calls the
**autonomy wrapper** "the Ralph Loop," but the experiment's own TL;DR says
*"quality comes from the gates, not the model"* — i.e. from the **convergence
machine**, which runs identically with or without the `while` loop.

## The harness, disassembled (verdicts are provisional — that's what the threads test)

```
  CONVERGENCE MACHINE  (makes output correct)             VERDICT
  ───────────────────────────────────────────             ───────
  spec → test → implement, no task without a spec   ████  load-bearing
  hard gates mirrored in CI (ruff/mypy/pytest)      ████  load-bearing
  pure rules core / value-driven seam               ████  load-bearing
  "progress = a commit" invariant                   ████  load-bearing
  independent review (Copilot re-derives principles) ███  high, underrated
  two-tier context (lean CLAUDE.md + on-demand)     ███   high
  milestone-gate sentinels                          ██    medium

  AUTONOMY WRAPPER  (makes it run unattended)             VERDICT
  ───────────────────────────────────────────             ───────
  while-true loop runner                            ██    medium → fading
  container sandbox (--dsp blast radius)            ██    medium (safety, not speed)
  stall-detector / timeout / N-no-commit halt       █?    only earns keep IF unattended
  model-by-risk routing                             ███   high (but done by hand now)
  fan-out harness                                   ▒     net-NEGATIVE at this scale
```

Every load-bearing component lives in the convergence machine. This is the
observation the threads interrogate.

---

## Thread A — What did "unattended" actually buy? `[PULLED — findings below]`

**Question:** Across M1–M11, tally wall-clock-saved-while-genuinely-away vs.
operator-thrash + diagnosis-tax incurred. Does the unattended loop come out net
positive even once? If not, that reframes the whole portable framework.

**Why it matters:** If autonomy was catalytic (forced the discipline into being)
rather than operational (sped up real work), the framework should ship the
convergence machine as the product and treat unattended execution as an opt-in
mode with explicit preconditions.

### Findings (2026-06-03 explore session)

1. **The record splits three ways.** Clean unattended: M4, M5 (Sonnet, gate-halt,
   the genuine wins); M6, M7 (clean but *Opus* — see #3). Needed human recovery:
   M3 (stall §5.10), M8 (timeout+outage §5.12), M9 (reboot). Net-negative: M10
   (fan-out). Not a loop at all: M11 (supervised-direct).

2. **You were optimizing throughput while your constraint was latency.** The
   field log says it twice (§3 M10 coda, §10 coda): *"the bottleneck was never
   turn throughput — it was the human-gate cycle and operator discipline."* The
   loop makes turns cheaper to *generate*; but turns were never the constraint —
   the PR→CI→review→merge cycle was. Autonomy attacked a non-bottleneck. The
   three moves that *did* pay (§10) all attack serial latency: batch milestones,
   auto-merge on clean review, model-by-task. None is "run unattended."

3. **Unattended converts cheap continuous supervision into expensive batched
   diagnosis.** A no-commit turn has indistinguishable causes (timeout exit 124 /
   limit-bounce exit 1 / reboot) — you must read the turn log to know which
   (§5.4 footnote). Supervised-direct has zero of this: you watch the failure
   happen. So autonomy doesn't remove operator attention; it *defers and batches*
   it into harder-to-diagnose episodes. And the Opus milestones (M6/M7) erode the
   cost argument from the other side: paying premium-model rates *and* standing by
   to recover means the "discount for sleeping" never materialized.

4. **M10 is the reductio.** Maximal autonomy (5 parallel loops) produced maximal
   thrash (§5.13–5.16). More autonomy → more coordination + diagnosis burden, not
   less. Meta-lesson §5.16: *resilience masks sloppiness* — the harness hid a bad
   operator without a red commit.

5. **You followed the gradient.** Drifting to supervised-direct by M11 wasn't a
   retreat; it was the rational response to 1–4. The same airtight convergence
   machine, run supervised, yields the same correctness without the wrapper's
   indirection (container parity §5.12, PROMPT/CI drift §5.1, host-rule blindness
   §5.11) or the diagnosis tax.

**Provisional verdict:** Unattended operation was a **forcing function** (catalytic
— it *required* the gates + commit-as-truth to exist, which is the real artifact)
and a **narrow-band optimizer** (real but small operational win on well-specified
pure-logic work *during genuine away-time*). It is **not** a general accelerator,
and at this project's unit size it mostly added indirection. Reach for unattended
execution only when ALL hold: (a) well-specified work, (b) model tier matched from
turn 1, (c) operator genuinely absent, (d) [parallel only] unit build-time
dominates per-unit coordination cost.

**Open sub-question for the user — RESOLVED (2026-06-03):** away-time is *real* —
the operator genuinely launches a run and leaves (hours/overnight). This upgrades
the operational value of unattended mode from "small" to "real **within its work
class**," and makes the four-precondition gate load-bearing.

### Sharpening: away-time is real AND we drifted to supervised-direct — both true

The apparent contradiction (the user leaves runs going, yet M11 was
supervised-direct) resolves cleanly: **the choice is work-class-driven, not a
wholesale verdict on autonomy.**

```
   WORK CLASS                          OPERATING MODE        EVIDENCE
   ─────────────────────────────       ──────────────        ────────
   well-specified pure-logic           LEAVE IT RUNNING      M4, M5 (clean,
   (faction config, henchmen rules)    (away-time pays)      Sonnet, gate-halt)

   stateful / object-lifecycle /       SUPERVISE DIRECTLY    M3 stall, M6/M7 Opus,
   integration / cross-zone wiring     (stalls if left)      M8/M9 recover, M11
```

M8–M11 were *all* bottom-row (stateful integration, parallel, stateful shrine),
so they correctly ran supervised. The earlier clean band (M4/M5) was top-row,
genuinely left running. **We didn't abandon unattended — we stopped mis-applying
it to work it was never good at.** This corrects one earlier finding: the
"diagnosis tax" is real but the true alternative to an overnight run is *zero
wall-clock*, not "watch it happen" — a genuine asymmetry underweighted above.

**Load-bearing framework primitive:** a **work-class classifier**. The single
decision *"is this milestone leave-it or supervise-it?"* subsumes BOTH the
model-by-risk rule (Sonnet vs Opus) AND the operating mode (unattended vs
supervised) — they are the same axis (well-specified-pure ↔ stateful-integration).
That is a cleaner primitive than two separate heuristics, and it feeds Thread B's
kernel directly.

---

## Thread B — What is the irreducible methodology kernel? `[PULLED — findings below]`

**Question:** Expressed as the *fewest rules* that still produce the quality, what
survives? Original candidate kernel (revised by the pull below):
1. No code without a failing test derived from a written spec.
2. A gate that mirrors CI exactly; you cannot commit red.
3. Progress is a commit; nothing partial is trusted.
4. An independent reviewer with no shared assumptions, every PR.
5. Match model to task type, set explicitly.

**Why it matters:** This is literally the methodology-vs-project-specific cut the
end-deliverable asks for.

### Findings (2026-06-03 explore session)

The candidate-5 failed the irreducibility test two ways.

**1. It was missing its integrity guards.** The list says *what to do* but omits
the rules that stop an optimizing agent from *routing around* the gate. Both are
already in locked CLAUDE.md §3; the draft dropped them:
- **Guard-A — don't invent the contract.** Spec silent → escalate
  (`questions.md`), never hallucinate a requirement. Without it, "spec is the
  contract" is hollow — the agent writes its own contract in the gaps.
- **Guard-B — don't game the proof.** Fix the *implementation* to pass
  verification, never the verification to pass the implementation ("never modify
  another subsystem's tests to make your code pass"). Without it, "cannot commit
  red" is theater.
  These are *adversarial* rules: they exist only because the agent is an optimizer
  whose cheapest path to "green" is often to weaken the thing measuring green.

**2. The kernel has structure, not a flat list — and it splits on a sharp line.**

```
   CONVERGENCE MACHINE  (methodology — portable)
   ① CONTRACT   spec → failing test → code (test = "done", spec = contract)
   ② PROOF      the commit is the atom of verified progress: nothing commits
                un-gated (gate ≡ CI exactly); nothing un-committed is trusted
   ③ REVIEW     independent, no shared assumptions, pre-merge — catches the
                "wired-wrong" class ①② cannot (Thread C)
   ④ GUARD-A    spec silent → escalate, never invent
   ⑤ GUARD-B    fix the code to pass, never the verification
   DISPATCH DIAL  (deployment — tunable)
   ⑥ WORK-CLASS classify each unit (well-specified-pure ↔ stateful-integration);
                class sets model tier AND supervision mode  ← Thread A's primitive
```

**3. Headline: correctness core vs. efficiency dial.** Re-running the removal
test, ①–⑤ are **correctness-irreducible** (remove one → quality drops in a way
nothing else catches). ⑥ is only **efficiency-irreducible** — remove it and you
get identical correctness by always choosing the safe option (always-Opus,
always-supervise); you just pay more. This *refines Thread A*: the work-class
classifier is load-bearing for **cost, not correctness** — mis-classifying never
yields a bad commit (the gate + commit-as-truth prevent it); a mis-classified
stateful job left running just stalls and commits nothing. The classifier buys
*cheaper* correctness, not *more*. That is why ①–⑤ are the machine and ⑥ is the
dial.

**Not in the kernel (enabling patterns / deployment, not methodology):**
- **Pure rules core / value-driven seam** — makes ① cheap (deterministic,
  Django-free tests). Project-specific.
- **Two-tier context (lean CLAUDE.md + on-demand)** — per-iteration *cost* +
  cache-stability optimization. Affects price, not correctness.
  Putting these in the kernel would conflate "makes output correct" with "makes
  producing it cheap" — exactly the cut this thread exists to make. They graduate
  to the *deployment* half of the framework.

**Graduation-ready:** the ①–⑤ correctness core + ⑥ dial split is solid enough to
seed the portable-framework spec's top-level structure (methodology = ①–⑤;
deployment = ⑥ + enabling patterns + the autonomy wrapper from Thread A).
Decision owner: the user, on whether to lock this structure.

---

## Thread C — Independent review may be a pillar, not a tip. `[PULLED — findings below]`

**Question:** Should the framework promote independent review from operational
tip to a named pillar? (B already answered *yes* on minimality — ③ is in the
correctness core. C's job: **what** class, **why** review catches it, **what** the
reviewer must be.)

**Why it matters:** If a whole failure class is invisible to gates, a framework
that sells "gates = safety" is selling an incomplete guarantee.

### Findings (2026-06-03 explore session)

**1. Pillar, not a finer filter — because it's orthogonal, not stronger.**
Verification splits into *assumption-preserving* (tests, mypy, ruff — "does the
code do what the author asserted, self-consistently?") and *assumption-challenging*
(review — "is what the author asserted even right, and wired correctly?"). These
are orthogonal, not stacked. You cannot substitute more of the first for the
second. This is the **oracle problem**: a test only checks what the author already
knew to assert; if the mental model is wrong, the test is wrong *in the same
direction* (M3 enum-vs-string: author thought enum → test stored enum → 11 green
tests, broken game). mypy/ruff are equally assumption-preserving. Review is the
*only* verification operating from a different prior. → answers the thread title:
**yes, pillar**, because it is the only filter of its kind.

**2. The mechanism IS the qualifier "no shared assumptions."** Copilot re-derived
this project's own principles (dice-seam, AC-duplication) with *no access to the
ADRs* — re-derived, not applied. Counterintuitive rule: **review value is inversely
related to how much of the author's mental model the reviewer shares.** A reviewer
given the ADRs would inherit the blind spots and catch less.

**3. Operational spec for the reviewer** (bounds the false-positive class — the two
wrong findings in the log were both claims about *external state* the reviewer
couldn't see):
- GIVE the full artifact (code + diff) — same facts, sees WHAT.
- WITHHOLD the author's intent/rationale (ADRs, "why") — different prior; let it
  re-derive/challenge the WHY.
- GIVE ground-truth external state it would otherwise guess at (CI results, config)
  — the wrong findings were ALL guesses about state outside the artifact. Pairs
  with the standing `defer-to-ground-truth` rule: verify external feedback before
  applying.

**4. The reviewer is a *property*, not a tool.** Pillar = "a cold, non-participant
reviewer with the artifact but not the intent." Copilot is one instance; a
fresh-context subagent (ralph-loop.md §6) and a human are others. The independence
that matters is *participation*, not architecture. Residual edge: same model family
for build+review may share *training-distribution* blind spots (e.g. a shared
hallucinated API) — unobserved here but not disproven; reviewer **diversity**
(different model / human) is the hedge for highest-stakes checks.

**5. Reconciles with Thread A.** A named the human-gate cycle the real bottleneck;
making review a pillar seems to worsen it. It doesn't — **auto-merge when the
reviewer is clean** (§10 move #2) makes review mandatory but *non-blocking when
clean*. Review only adds latency when it has a finding worth judgment.

**Taxonomy — what review catches that gates can't:**
| # | Class | Instance | Why tests miss it |
|---|---|---|---|
| 1 | Shared-assumption bug | enum-vs-string (M3) | test encodes the same wrong premise → green *and* wrong |
| 2 | Integration-gap bug | dice-seam, dead spell-disruption (M2) | units pass; nothing exercises the path between them |
| 3 | Global-property bug | isolation leak (M10), leaderboard (M5+M6) | true only of the union; no PR's scope sees it |
| 4 | SSOT / duplication drift | AC formula in `Mob.computed_ac` (M2) | all tests pass until the two copies diverge |
| 5 | *(reviewer's own)* external-state false positive | false CI-lint & mypy claims | reviewer can't see state outside the artifact → feed ground truth, verify |

**Graduation-ready:** review graduates into the methodology half as pillar ③, with
the operational spec (#3) and the property-not-tool framing (#4) attached.

---

## Thread D — Operator discipline as a first-class artifact. `[PULLED — findings below]`

**Question:** §5.16's meta-lesson — *resilience masks sloppiness* — means the
harness hides a bad operator. Should the framework ship an operator-discipline
artifact as a peer to the loop mechanics?

**Why it matters:** A methodology robust enough to hide its own misuse needs an
explicit guard against that misuse, or it teaches bad habits that surface at scale.

### Findings (2026-06-03 explore session)

**1. The operator is the only role with no gate.** Builder failures are *blocked*
(gate ② + guards ④⑤); reviewer failures *surface as findings* (③); operator
failures (launching, killing, triaging, theorizing) are **invisible**, because
those actions aren't commits and the machine's instrument is the commit graph.

**2. Structural cause — the shadow of rule ②.** "Progress = a commit" makes the
machine durable, but its corollary is that *anything that isn't a commit is
invisible to the methodology's main instrument.* Operator thrash is by definition
non-commit activity → invisible. M10 proves it: an hour of runaway containers +
brute-force loops + four wrong theories produced **zero red commits, zero lost
work.** Output quality and operator discipline are therefore **decoupled** — you
cannot infer one from the other; you need a separate signal.

**3. Two faces, already in the memory store (unconsolidated).**
- EPISTEMIC (don't act on unverified belief): triage-before-brute-force (§5.14),
  defer-to-ground-truth (§5.16).
- PROCEDURAL (manage the environment cleanly): bg-process-hygiene (§5.15),
  constraints-in-prompt-not-filesystem + one-orchestrator (§5.13); also
  push-cadence, pr-flow.
  → D's real contribution: these exist as *scattered* memories; name them as **one
  coherent layer**.

**4. Framework implication — a THIRD layer, with no teeth.**
```
  1. CONVERGENCE MACHINE (①–⑤)  protects the ARTIFACT     ENFORCEABLE (gate blocks)
  2. DISPATCH + DEPLOYMENT (⑥…) tunes COST/throughput     CONFIGURABLE (you choose)
  3. OPERATOR DISCIPLINE        protects the PROCESS from CHECKLIST-ONLY (nothing
                                its own operator           blocks you)
```
Layer 3 is the one part the framework **cannot enforce** (operator actions aren't
commits). Teeth substitutes: (a) *instrument the operator* (PR #2 observability =
make non-commit state legible so thrash is visible); (b) *pre-action checklists* at
the high-risk moments (before backgrounding a job; before reproducing a failure;
before asserting a causal "why").

**5. Frontier framing (why now).** Builder is automated (the loop); reviewer is
automated (Copilot); **the operator is the last human-ish role and the one with no
gate.** Current mode (supervised-direct) means the operator is *already an agent* —
§5.16 was the supervising agent spinning wrong theories, not a human. So this is
**agent-operator discipline**: same failure modes, less self-awareness. As the role
automates, discipline must move from "human remembers" → *encoded constraints +
instrumentation*, the same trajectory the builder's rules took at §5.11.

**6. Honesty requirement.** A method that demos clean *while concealing operator
thrash* gets adopted on that demo, then fails in hands with worse operator
discipline and no checklist. Shipping layer 3 is an integrity requirement, not a
nicety — otherwise the framework's success quietly depends on an unstated,
unmeasured skill.

**Graduation-ready:** operator discipline becomes the framework's **third layer**,
seeded by consolidating the existing operator memories under the
epistemic/procedural split, with the instrument + checklist substitutes for the
missing gate.

---

## Synthesis — all four threads pulled (2026-06-03)

The four threads resolve into a **three-layer framework**, which is the
methodology-vs-project-specific cut the end-deliverable asked for:

```
  LAYER 1 — CONVERGENCE MACHINE   (methodology, portable, ENFORCEABLE)
    ① contract  ② proof  ③ review  ④ guard-A (don't invent)  ⑤ guard-B (don't game)
    [B made the structure; C made ③ rigorous]

  LAYER 2 — DISPATCH + DEPLOYMENT (tunable, CONFIGURABLE)
    ⑥ work-class dial (model tier + supervision mode)  [A]
    enabling patterns (pure rules core, two-tier context)  [B]
    autonomy wrapper (loop runner, container, fan-out) — opt-in, gated on
      A's 4 preconditions; value was mostly catalytic + narrow-band  [A]

  LAYER 3 — OPERATOR DISCIPLINE   (methodology, UNENFORCEABLE — checklist+instrument)
    epistemic: triage-before-brute-force, defer-to-ground-truth
    procedural: bg-process-hygiene, constraints-in-prompt, one-orchestrator
    [D — the layer the machine structurally cannot see]
```

Cross-thread spine: **correctness lives in Layer 1 (enforceable); cost lives in
Layer 2 (configurable); the blind spot is Layer 3 (unenforceable).** A's classifier
buys *cheaper* correctness not *more* (B). C's review is the only Layer-1 filter of
its kind (orthogonal, not stronger). D is Layer 1's shadow — the operator the
commit-graph instrument cannot measure.

**Next step when ready:** graduate this synthesis into an actual portable-framework
spec (OpenSpec change), splitting the three layers into methodology (1, 3) vs
project-specific deployment (2). Not yet locked — pending user direction.

---

## How to use this doc

Pull one thread per explore session. Record findings inline under the thread (as
done for A). When a thread's conclusion is solid enough to act on, it graduates
into either the portable-framework spec (methodology) or `ralph-loop.md`
(project-specific deployment). This doc is the staging area between *noticing* and
*locking*.
