# Layer 2 — Dispatch + Deployment

**Protects:** cost / speed · **Enforceable:** configurable ·
**Kind: mostly deployment (project-specific) — re-tune this layer per project.**

Layer 1 makes the artifact *correct*. Layer 2 makes getting there *cheap and fast*.
Nothing here can break correctness — that's the load-bearing claim of the whole
layer (see §"cost, not correctness"). The *principles* are portable; the concrete
answers (which model, which container, which commands) are tuned per project and
toolchain, so most of this layer is tagged **deployment**.

> Spec contract: `openspec/changes/ralph-framework-v1/specs/work-dispatch/spec.md`.

---

## ⑥ The work-class dial — *configurable*

**Classify each unit of work on one axis — `well-specified-pure ↔
stateful/integration` — and let that class set BOTH the model tier AND the
supervision mode.** Model-by-risk and operating-mode are the *same decision*, set
explicitly per unit, **never "auto."**

| Work class | Model tier | Supervision |
|---|---|---|
| **Stateful / object-lifecycle / cross-subsystem / config-critical wiring** | stronger model, **from turn 1** | supervise directly |
| **Well-specified pure logic** (detailed spec, deterministic tests) | cheaper model | may run unattended *(if Layer-2 preconditions hold)* |

Assign the stronger model to stateful work *from turn 1* to avoid **stall-then-
escalate waste** — starting cheap, thrashing, then upgrading mid-task burns a turn
(field log §5.10; §3 M6). Pure, well-specified logic runs cheaply (field log M4/M5).

*The classifier is portable; the dispatch table — which model maps to which class,
when to watch — is project- and toolchain-specific.* That's why ⑥ is **configurable**.

## Cost, not correctness — *methodology*

**The dial buys *cheaper* correctness, not *more* correctness.** A misclassification
must never be able to produce an incorrect *committed* artifact — at worst it stalls
and commits nothing, because the [convergence machine](layer-1-convergence-machine.md)
(gate + commit-as-truth) remains the correctness guarantee.

> Run stateful work wrongly as "pure + unattended + cheap model" → worst case is a
> **stalled turn with no commit** (caught by the stall detector), never a bad commit
> reaching main. Cost is paid in clock, not quality.

This principle is **methodology**: the dial is an *efficiency lever, not a
correctness lever* — true on any project. It's what makes it safe to tune Layer 2
aggressively.

## Velocity targets serial latency, not turn throughput — *methodology*

**The real bottleneck is the human-gate cycle** (PR → CI → review → fixes → merge),
**not turn throughput.** Direct velocity effort at *serial latency*:

- batch clean milestones per PR (fewer human round-trips);
- auto-merge when the independent reviewer is clean (Layer 1 ③);
- match model to task type (⑥).

**Parallelize the independent units the architecture produces — not the convergence
loop itself.** The impulse "more containers / more agents on the same milestone"
fails: systems-layer work shares files and collides; turn throughput was never the
constraint (field log §10). This is **methodology** — the diagnosis carries to any
project.

---

## The autonomy wrapper — *configurable, opt-in, gated*

Unattended execution — the loop runner, container sandbox, and any fan-out — is an
**opt-in deployment mode, not the default.** Invoke it only when **all four**
preconditions hold:

1. **The work is well-specified** (a real spec + deterministic tests).
2. **The model tier is matched from turn 1** (no mid-task escalation).
3. **The operator is genuinely absent** — away-time is real, otherwise-idle
   wall-clock, not "watching it run."
4. **(Fan-out only)** a single unit's build time **dominates** its per-unit
   coordination cost.

If *any* precondition is false → build **supervised-direct**; do not invoke
unattended mode.

> **Thread A's verdict (the honest finding).** In evidence, the unattended loop was
> **catalytic and narrow-band, not a general accelerator.** It attacked a
> *non-bottleneck* (turn throughput) while the real constraint was the human-gate
> cycle. Presenting autonomy as a turnkey speedup would be the framework lying about
> its own evidence (eval Thread A, derived from field log §10 and §3 M10). Away-time is a real
> operating condition, so the *gated opt-in mode* earns documentation — but it is not
> the headline.

### Fan-out (parallel content) — serial-by-default

When independent *content* units (not systems work) are fan-out candidates: treat
fan-out as **serial-by-default with opt-in only**, reached for **only** when per-unit
build time dominates coordination cost (precondition 4). The reference
implementation here was **net-negative at small unit size** and is **not a turnkey
speedup**: tribe loops drifted past their scoped task lists, a discovery aggregator
silently re-shared a test file, "all PRs green" did not mean main was green, and the
clone/container/per-PR overhead outweighed the parallelism (field log §3 M10,
§5.13–5.16). The *idea* is sound; that *implementation* needs rework before reuse
(scoped task lists enforced, no shared-file aggregation, verify main-green after
landing — not just per-PR-green).

---

## Enabling patterns — *configurable*

Practices that make the Layer-1 contract *cheap to satisfy*. Distinct from the
correctness rules themselves; their shape depends on the stack, so they're
**deployment**:

- **A pure, framework-free rules core with a value-driven test seam.** Isolate the
  most bug-prone logic from the runtime/framework so it can be unit-tested *without
  booting the runtime* — fast, deterministic, strict-typed. This lowers the cost of
  ① spec-first (tests are cheap to write and run).
- **Two-tier context layout.** A lean, always-loaded instruction file (paid every
  iteration) + on-demand depth docs (loaded only when a task needs them). Keeps the
  per-turn context cost down without losing the depth.

---

## What's portable vs. what you re-tune

| Element | Tag |
|---|---|
| The work-class **classifier** (one-axis: pure ↔ stateful) | methodology (the axis) |
| The **dispatch table** (which model, when to supervise) | deployment |
| Dial buys cost, not correctness | **methodology** |
| Velocity targets serial latency, not throughput | **methodology** |
| Autonomy wrapper + its 4 preconditions (the *gate* is portable; the *tooling* isn't) | deployment |
| Enabling patterns (pure core, two-tier context) | deployment |

The methodology rows you keep; the deployment rows you decide fresh for each
project's stack and operating conditions.
