## Why

This project was always two deliverables: the B2 MUD, and a **portable Ralph-loop
framework** distilled from how it was built (the standing end-goal in project
memory `ralph-framework-goal`). After eleven milestones, a first-principles
evaluation (`docs/ralph-loop-evaluation.md`, threads A–D) crystallized the
methodology into a clean three-layer structure with a sharp methodology-vs-
deployment cut. That structure is now stable enough to **graduate from a field log
and scattered memories into a versioned spec** a future project can adopt without
re-deriving it.

## What Changes

- Add a **portable framework playbook** under `docs/framework/` — the
  human-facing, project-agnostic deliverable — organized as three layers:
  1. **Convergence machine** (Layer 1): contract → proof → review, guarded by
     "don't invent the contract" and "don't game the verification". *Correctness;
     enforceable; methodology.*
  2. **Dispatch + deployment** (Layer 2): the work-class dial (model tier +
     supervision mode), enabling patterns (pure rules core, two-tier context), and
     the autonomy wrapper (loop runner, container, fan-out) as an opt-in mode gated
     on explicit preconditions. *Cost; configurable; project-specific.*
  3. **Operator discipline** (Layer 3): epistemic + procedural discipline — the one
     layer the gate structurally cannot enforce, given teeth by instrumentation +
     pre-action checklists. *Process integrity; unenforceable; methodology.*
- Capture the **cross-cutting findings** as first-class framework claims, not
  buried lessons: (A) the unattended loop was catalytic + narrow-band, not a
  general accelerator — the real bottleneck was the human-gate cycle, not turn
  throughput; (B) the work-class dial buys *cheaper* correctness, not *more*; (C)
  independent review is an *orthogonal* pillar (assumption-challenging), not a finer
  filter of the same kind.
- Mark each framework element **methodology (portable)** vs **deployment
  (project-specific)** — the split is the spine of the deliverable.
- **No runtime code.** This change produces specs + documentation only. The field
  log (`docs/ralph-loop-experiment.md`) and evaluation backlog
  (`docs/ralph-loop-evaluation.md`) remain the evidence base and are cross-linked,
  not duplicated.

## Capabilities

### New Capabilities
- `convergence-machine`: The enforceable correctness core — spec→test→implement
  contract, the commit-as-verified-progress proof (gate ≡ CI), independent review
  as an orthogonal pillar, and the two integrity guards that keep an optimizing
  agent from routing around the gate. (Layer 1; methodology.)
- `work-dispatch`: The configurable deployment layer — the work-class classifier
  that sets both model tier and supervision mode, the enabling patterns, and the
  autonomy wrapper as an opt-in mode with its four preconditions. (Layer 2;
  project-specific/configurable.)
- `operator-discipline`: The unenforceable process-integrity layer — the
  epistemic and procedural discipline the commit-graph instrument is blind to, with
  the instrument + checklist substitutes for the missing gate. (Layer 3;
  methodology.)

### Modified Capabilities
<!-- None. This is a new, project-agnostic framework capability set; it does not
     change any B2 MUD subsystem requirement. -->

## Impact

- **New files only** — `docs/framework/` playbook + the three OpenSpec capability
  specs. No runtime code, no test changes, no dependency changes.
- **Quality gates**: markdown is outside ruff/mypy; no executable additions, so CI
  is unaffected.
- **Cross-references** `docs/ralph-loop-evaluation.md` (threads A–D, the
  derivation), `docs/ralph-loop-experiment.md` (the field-log evidence), the ADRs
  in `docs/decisions/`, and the locked patterns in `CLAUDE.md` §3. Does not reopen
  any locked decision.
- **Downstream**: becomes the artifact a *future* project imports as defaults
  ("answer once, reuse"); the methodology layers (1 & 3) carry over wholesale, the
  deployment layer (2) is re-tuned per project.
