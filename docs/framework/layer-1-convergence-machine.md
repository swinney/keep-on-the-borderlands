# Layer 1 — The Convergence Machine

**Protects:** correctness of the artifact · **Enforceable:** yes (the gate) ·
**Kind: methodology (portable) — copy this layer verbatim.**

This is why the loop converges instead of drifting. Five rules: three that define
and prove correctness (contract → proof → review) and two integrity guards that stop
an optimizing agent from routing around them. Every rule here is **methodology** and
portable to any project and stack.

> Spec contract: `openspec/changes/ralph-framework-v1/specs/convergence-machine/spec.md`.

---

## ① Spec-first contract — *methodology*

**No unit of work starts before a written spec exists and a test derived from that
spec exists and fails.** The failing test is the definition of "done"; the spec is
the contract the implementation must not silently drift from.

- Pick a task whose subsystem has **no spec** → write the spec first (or escalate);
  do **not** write implementation in the same step.
- Spec exists but **no test** → author the failing test from the spec's scenarios
  *before* implementing, so "done" is defined before it's pursued.

*Why it's irreducible:* without it, "done" is whatever the model decides mid-stream,
and the artifact drifts from intent with nothing to catch the drift.

## ② Commit as the unit of verified progress — *methodology*

**A commit is the only proof that real, gated work happened.** Three sub-rules:

1. **The local gate mirrors CI exactly and in the same order.** Same checks, same
   sequence (e.g. `format-check → lint → types → tests`). A locally-green commit
   must be unable to go CI-red. When they diverge, that's a *defect to fix*, not a
   nuisance to tolerate (field log §5.1 — a missing `ruff format` check let a red
   commit through on the very first supervised turn).
2. **Cannot commit red.** The agent is structurally unable to commit a failing gate.
3. **Nothing uncommitted is progress.** A turn killed (timeout, outage, reboot) with
   a clean-but-uncommitted tree assumed *zero* progress: recovery re-runs the gate
   and either commits the surviving work or retries. **Killed turns cost only clock,
   never work** (field log §5.8).

*Why it's irreducible:* the commit graph is the one trustworthy record. If
uncommitted state counted, every crash would corrupt the ledger.

## ③ Independent review as an orthogonal pillar — *methodology*

**Every code change gets an independent reviewer with no shared mental model, before
merge.** This is not "more tests" — it is a *different kind* of check.

- Tests, types, and lint are **assumption-preserving**: they verify the code against
  the author's own premises. If the code and its tests share a wrong premise, they
  all pass and the behavior is still wrong.
- Review is **assumption-challenging**: a reviewer operating from a *different prior*
  catches the **"wired-wrong" class** — e.g. a field treated as an enum that the
  system actually stores as a string; every test green, behavior wrong (field log
  §5.9). No amount of same-kind checking reaches this class.

Operating rules for review (eval Thread C):

- **Give the reviewer the full artifact and ground-truth external state; withhold the
  author's intent/rationale.** Supplying the intent re-shares the mental model and
  collapses the orthogonality.
- **Verify the reviewer's external-state claims against ground truth.** If a reviewer
  asserts something it cannot observe from the artifact ("this fails CI" with no CI
  access), that claim is the reviewer's *own* failure class — check it before acting.
- **A clean review must not gate latency.** Reviewer returns zero findings + CI green
  → the change *may* auto-merge with no human round-trip. Review blocks only when a
  finding needs judgment. (This reconciles review-as-pillar with the fact that the
  human-gate cycle is the real bottleneck — see [Layer 2](layer-2-dispatch-and-deployment.md).)

*Why it's irreducible:* it's the only filter that catches the wired-wrong class.
Drop it and a whole category of bugs ships green.

---

## The two integrity guards

A gate only works if the agent can't optimize around it. These two guards are what
keep ① – ③ honest.

## ④ Guard: don't invent the contract — *methodology*

**When the spec is silent, escalate to the human — do not hallucinate a
requirement.** The agent is a *builder, not an architect*. A decision the spec
doesn't cover gets recorded as a question and the agent stops, rather than inventing
and encoding an unauthorized requirement.

*Why it's irreducible:* without it, the agent fabricates the contract it's supposed
to be held to — and then satisfies its own fabrication. The gate passes; the product
is wrong.

## ⑤ Guard: don't game the verification — *methodology*

**Change the implementation to satisfy the verification, never the verification to
pass the implementation.** The agent must not weaken or edit another unit's tests,
the gate, or the spec to turn red green. When a failing test blocks a commit, fix the
*implementation* (or escalate a genuine spec error) — never edit the test or spec to
make the failure vanish.

*Why it's irreducible:* this is what keeps "cannot commit red" from being hollow.
Without it, "green" just means "the agent moved the goalposts."

---

## Putting Layer 1 together

```
   spec  ──►  failing test  ──►  implementation  ──►  local gate (≡ CI)  ──►  commit  ──►  independent review  ──►  merge
    │              │                                      │                                      │
  guard ④      contract is                          cannot commit red                    orthogonal pillar:
 (don't        the definition                       (guard ⑤: don't                       catches wired-wrong
  invent)        of done                             game it)                              (assumption-challenging)
```

The loop *converges* because every step narrows toward a contract the agent didn't
write and can't quietly rewrite, proven by a commit it can't fake, checked by a
reviewer it can't align. That is the whole correctness story — and all of it is
portable methodology. Cost and speed are a **separate** concern
([Layer 2](layer-2-dispatch-and-deployment.md)); the one thing this machine *cannot*
see is the operator who runs it ([Layer 3](layer-3-operator-discipline.md)).
