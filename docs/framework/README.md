# The Ralph-Loop Framework (v1)

A portable, project-agnostic playbook for building software with an LLM agent in a
spec-driven loop. Distilled from the *Keep on the Borderlands* build (eleven
milestones) and pruned by a first-principles **irreducibility test** — *remove a
rule; does something degrade that nothing else catches?* What survived is here.

> **v1 honesty note.** This is distilled from **one** project (N=1). The
> methodology layers (1 and 3) are claimed to carry over wholesale; the deployment
> layer (2) is explicitly project-specific and re-tuned each time. The first real
> validation is the *next* project — treat v1 as defaults to pressure-test, not law.

## The three layers

The methodology resolves into three layers, separated along **two axes**: *what each
layer protects*, and *whether the harness can enforce it*.

| Layer | Protects | Enforceable? | Kind |
|---|---|---|---|
| **1 — Convergence machine** | correctness of the artifact | **yes** (the gate) | **methodology** (portable) |
| **2 — Dispatch + deployment** | cost / speed | configurable | **deployment** (project-specific) |
| **3 — Operator discipline** | process integrity | **no** (structural blind spot) | **methodology** (portable) |

```
  LAYER 1 — CONVERGENCE MACHINE   (methodology · portable · ENFORCEABLE)
    ① contract  ② proof (commit ≡ gate ≡ CI)  ③ independent review
    ④ guard: don't invent the contract   ⑤ guard: don't game the verification

  LAYER 2 — DISPATCH + DEPLOYMENT  (deployment · project-specific · CONFIGURABLE)
    ⑥ work-class dial (model tier + supervision mode, set per unit, never "auto")
    enabling patterns (pure rules core · two-tier context)
    autonomy wrapper (loop runner · container · fan-out) — OPT-IN, gated on 4 preconditions

  LAYER 3 — OPERATOR DISCIPLINE    (methodology · portable · UNENFORCEABLE — checklist + instrument)
    epistemic: triage-before-brute-force · defer-to-ground-truth
    procedural: no bare-& jobs · constraints-in-prompt · one-orchestrator
```

**The spine in one line:** correctness lives in Layer 1 (enforceable); cost lives in
Layer 2 (configurable); the blind spot is Layer 3 (unenforceable). Layer 2's dial
buys *cheaper* correctness, not *more*. Layer 1's review is an *orthogonal* pillar,
not a finer filter. Layer 3 is Layer 1's shadow — the operator the commit-graph
instrument cannot measure.

## How to read this playbook

- **[Layer 1 — Convergence machine](layer-1-convergence-machine.md)** — the
  enforceable correctness core. The part you copy verbatim.
- **[Layer 2 — Dispatch + deployment](layer-2-dispatch-and-deployment.md)** — the
  cost dial and the opt-in autonomy wrapper. The part you re-tune per project.
- **[Layer 3 — Operator discipline](layer-3-operator-discipline.md)** — the
  unenforceable process layer, with its checklist + instrument teeth-substitutes.
- **[Quickstart](quickstart.md)** — the one-page "answer-once defaults" a new
  project imports, plus the three pre-action checklists.
- **[Ralph Harness Kit](../../ralph-harness/README.md)** — the *runnable* Layer-2
  autonomy wrapper: copyable, config-driven loop runner + container + templates
  (`ralph-harness/`). This playbook is the *why*; the kit is the *how to run it*.

## Legend

Every element below carries one tag:

- **methodology (portable)** — carries to any project unchanged. Layers 1 and 3.
- **deployment (project-specific / configurable)** — the *principle* is portable but
  the concrete answer (which model, which container, which commands) is re-tuned per
  project and toolchain. Layer 2.

An adopter reads the tags to know what to copy (methodology) vs. what to decide
(deployment).

## Cross-link convention (evidence, not duplication)

This playbook is **distilled from**, and **cross-links to**, two living source docs
in this repo. It does **not** duplicate them — duplication rots, and the sources are
the single source of truth (a Layer-1 value the framework eats its own dogfood on):

- **`docs/ralph-loop-experiment.md`** — the field log: the war stories and metrics
  that are the *evidence* for every claim here. Cited as **§N** (e.g. §5.9).
- **`docs/ralph-loop-evaluation.md`** — the first-principles evaluation: the
  *derivation* of the three-layer structure, in four threads **A–D** (now graduated
  into this framework).

When a claim cites `(field log §5.9)` or `(eval Thread C)`, follow the link for the
concrete incident. New evidence accrues in those docs and flows through by reference
— this playbook references sections, so it doesn't need editing as the log grows.

The OpenSpec contract behind this playbook is the `ralph-framework-v1` change
(capability specs `convergence-machine`, `work-dispatch`, `operator-discipline`);
the playbook is the human-usable artifact, the specs are the testable contract.
