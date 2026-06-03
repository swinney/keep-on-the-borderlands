# Quickstart — Answer-Once Defaults

The one page a new project imports. These are the **methodology defaults** (copy as-is)
plus the **deployment decisions** you make once per project. Full rationale lives in
the layer docs; this is the reuse surface.

For the *why* behind any line, follow it to [Layer 1](layer-1-convergence-machine.md),
[Layer 2](layer-2-dispatch-and-deployment.md), or [Layer 3](layer-3-operator-discipline.md).

---

## The kernel rules (methodology — copy verbatim)

**Layer 1 — convergence machine (correctness, enforceable):**

1. **Spec-first.** No work without a written spec + a failing test derived from it.
   The test is "done."
2. **Commit ≡ gate ≡ CI.** The local gate mirrors CI exactly and in order; the agent
   *cannot commit red*; uncommitted = not progress (killed turns cost clock, not work).
3. **Independent review, every change, before merge.** A reviewer with no shared
   mental model. Give it the artifact + ground-truth state; **withhold the intent.**
   It catches the wired-wrong class tests can't. Clean review + green CI → may
   auto-merge.
4. **Guard — don't invent the contract.** Spec silent → escalate, don't hallucinate a
   requirement. (Builder, not architect.)
5. **Guard — don't game the verification.** Fix the implementation to pass the test;
   never edit the test/spec/gate to pass the implementation.

**Layer 3 — operator discipline (process, unenforceable — so checklist it):**

6. Output quality is **not** evidence of discipline. Run the pre-action checklists
   below.

## The dispatch table (deployment — decide per project)

Fill this in for your stack and models:

| Work class | Model tier | Supervision |
|---|---|---|
| Stateful / integration / config-critical | `<stronger model>` from turn 1 | supervise directly |
| Well-specified pure logic | `<cheaper model>` | unattended *iff* the autonomy gate passes |

- Set model tier **and** supervision mode together, per unit, **never "auto."**
- The dial buys **cheaper** correctness, not more — a misclass at worst *stalls*,
  never ships a bad commit.
- Velocity effort → **serial latency** (batch milestones per PR, auto-merge on clean
  review), **not** parallelizing the loop.

## The autonomy precondition gate (deployment — checklist before going unattended)

Unattended (loop runner / container / fan-out) is **opt-in**. Go unattended only if
**all** are true; otherwise build supervised-direct:

- [ ] **Well-specified** work (real spec + deterministic tests)?
- [ ] **Model matched from turn 1** (no planned mid-task escalation)?
- [ ] **Operator genuinely absent** (real idle wall-clock, not "watching")?
- [ ] **(Fan-out only)** single-unit build time **dominates** per-unit coordination cost?

> Evidence verdict: unattended operation was **catalytic + narrow-band, not a general
> accelerator.** The bottleneck is the human-gate cycle, not turn throughput. Don't
> reach for autonomy to "go faster" by default.

---

## The three pre-action checklists (Layer 3 teeth)

The only substitute for a gate the harness can't provide. Run the matching one
*before* the action. (Copy-pasteable.)

<a id="checklist-1"></a>

### Checklist 1 — before backgrounding a job

- [ ] Launched through a **tracked, named, killable-by-id** mechanism (not a bare `&`)?
- [ ] I know the **exact cleanup command** before I start it?
- [ ] It's the **only** orchestrator of its kind running (no competing loop/sweep)?
- [ ] After it ends, I will verify clean with a **broad** process check (not a
      name-prefix grep that auto-named jobs slip)?

<a id="checklist-2"></a>

### Checklist 2 — before reproducing a failure

- [ ] **Possible from the code?** I read the implementation first.
- [ ] **Infra artifact?** I checked the harness (concurrency, shared vs. isolated DB).
- [ ] **Worth it?** A rare flake in a *test* may not justify blocking now.
- [ ] If I do reproduce, I'll make it **deterministic** so a hit is permanent, then
      instrument once and fix.

<a id="checklist-3"></a>

### Checklist 3 — before asserting a causal "why" about an external system

- [ ] Do I have **direct proof**, or am I **inferring** from timestamps / partial output?
- [ ] If inferring, I will **say so** ("the timestamps *suggest* X, but you'd know")
      and stop — not assert a tidy narrative.
- [ ] If the user has stated a fact about **their own** setup/actions, that is **ground
      truth**; I won't counter it with an API-derived theory.
- [ ] Am I over-generalizing **one anecdote** over the user's general statement of how
      their system is configured?

---

## Adopting on a new project

1. Copy the **kernel rules** (Layers 1 + 3) verbatim — they're methodology.
2. Decide the **deployment** rows (dispatch table, autonomy tooling) for your stack.
3. Stand up the **gate ≡ CI** first (rule 2) — nothing else works without it.
4. Wire an **independent reviewer** into the merge path (rule 3).
5. Keep this framework honest: it's distilled from **one** project. Pressure-test it
   here, and feed back what breaks.
