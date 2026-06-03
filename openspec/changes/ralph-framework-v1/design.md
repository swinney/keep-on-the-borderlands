## Context

The methodology was built bottom-up: locked patterns in `CLAUDE.md` §3, a running
field log (`docs/ralph-loop-experiment.md`), scattered operator memories, and ADRs.
The first-principles evaluation (`docs/ralph-loop-evaluation.md`) ran the
**irreducibility test** on all of it — *remove a rule; does something degrade that
nothing else catches?* — and the survivors organized into three layers along two
axes: **what they protect** (artifact / cost / process) and **whether the harness
can enforce them** (enforceable / configurable / unenforceable). This change turns
that evaluated structure into the portable deliverable. The evidence already
exists; the work here is *organization and the methodology-vs-deployment cut*, not
new discovery.

## Goals / Non-Goals

**Goals:**
- A project-agnostic playbook under `docs/framework/` a future project imports as
  defaults — "answer once, reuse."
- A clean **methodology (portable) vs deployment (project-specific)** tag on every
  element, so an adopter knows what carries over wholesale (layers 1 & 3) vs what
  they re-tune (layer 2).
- Three OpenSpec capability specs (one per layer) stating requirements in
  testable-claim form, each traceable to field-log evidence.
- Preserve the *honest* findings (A/B/C/D), including where autonomy under-
  delivered — the framework's credibility depends on not overselling the loop.

**Non-Goals:**
- No runtime code, no tooling, no scripts. (The existing `scripts/ralph.sh`,
  `Containerfile`, fan-out harness stay as the deployment-layer *reference
  implementation*, not re-authored here.)
- Not extracting the framework into a separate repo yet — that is a future step;
  v1 lands it in-repo under `docs/framework/`.
- Not reopening any locked B2/MUD decision; this layer is orthogonal to game
  content.

## Decisions

**D1 — Three capability specs mapped 1:1 to the layers** (`convergence-machine`,
`work-dispatch`, `operator-discipline`), rather than one monolithic `framework`
spec. *Why:* the layers differ in enforceability and portability, so they have
genuinely different requirement *kinds* (Layer 1 = "the gate MUST block X"; Layer 3
= "the operator SHOULD checklist Y, since nothing can block them"). Splitting keeps
each spec's modality coherent. *Alternative rejected:* a single spec blurs the
enforceable/unenforceable distinction that is the evaluation's sharpest finding.

**D2 — The deliverable is a human playbook (`docs/framework/`) backed by the specs**,
not the specs alone. *Why:* the audience is a human (or agent) starting a *new*
project; they need narrative + the answer-once defaults, not just acceptance
criteria. The OpenSpec specs are the contract; the playbook is the usable artifact.
*Alternative rejected:* specs-only — too terse to adopt from cold.

**D3 — Evidence stays in the field log; the framework cross-links, never
duplicates.** Each requirement cites its field-log section (e.g. the enum-vs-string
catch → §5.9, the M10 thrash → §5.13–5.16). *Why:* duplication rots; the field log
is the living source. *This is the framework eating its own dogfood* (single source
of truth, a Layer-1 value).

**D4 — Autonomy wrapper is documented as opt-in, gated on four preconditions**
(well-specified work · model matched from turn 1 · genuine operator away-time ·
[parallel] unit build-time dominates coordination cost), with Thread A's verdict
attached: catalytic + narrow-band, not a general accelerator. *Why:* the honest
finding is that the loop attacked a non-bottleneck (turn throughput) while the real
constraint was the human-gate cycle. Presenting autonomy as a turnkey speedup would
be the framework lying about its own evidence. *Alternative rejected:* dropping the
wrapper entirely — away-time is a real operating condition (resolved with the user),
so the gated opt-in mode earns documentation.

**D5 — Operator discipline ships with its own teeth-substitutes**, because the gate
cannot reach it: (a) instrument the operator (surface non-commit state), (b)
pre-action checklists at the three high-risk moments (background a job / reproduce a
failure / assert a causal "why"). *Why:* a layer named but left toothless would
degrade silently — the exact "resilience masks sloppiness" failure it exists to
prevent.

## Risks / Trade-offs

- **The framework demos clean while concealing operator thrash** → adopters with
  worse operator discipline fail where this project didn't. *Mitigation:* Layer 3 is
  a first-class, mandatory part of the spec, not an appendix; the honesty risk is
  named explicitly in the playbook (D's finding #6).
- **Premature generalization** — N=1 project, generalizing to "any project." →
  *Mitigation:* tag confidence; mark layer 2 explicitly project-specific; frame v1
  as distilled-from-one-build, to be pressure-tested on the next project (that test
  is itself the framework's first real validation).
- **Spec/playbook drift from the field log** as future milestones (M12–M14) add
  evidence. → *Mitigation:* D3's cross-link-don't-duplicate rule; the playbook
  references sections, so new field-log entries flow through without edits here.
- **Over-formalizing kills adoption** — too many rules and nobody uses it. →
  *Mitigation:* the irreducibility test already pruned to a minimal kernel (5
  correctness rules + 1 dial + 2 discipline faces); resist re-inflating.

## Open Questions

- Does layer 2's autonomy wrapper deserve a worked precondition *checklist*
  (decision-tree) in v1, or just the four-criterion gate? (Lean: gate now,
  decision-tree when a second project tests it.)
- Should the playbook carry a one-page "answer-once defaults" quick-start distinct
  from the per-layer detail? (Lean: yes — it is the highest-value page for reuse.)
