# work-dispatch Specification

## Purpose
TBD - created by archiving change ralph-framework-v1. Update Purpose after archive.
## Requirements
### Requirement: Work-class classification drives dispatch

The framework SHALL classify each unit of work on a single axis —
well-specified-pure ↔ stateful/integration — and let that class set BOTH the model
tier (cheaper model for pure logic, stronger model for stateful/config-critical/
integration work) AND the supervision mode (may run unattended vs. supervise
directly). Model-by-risk and operating-mode are the same decision, set explicitly
per unit, never "auto." This requirement is **configurable (project-specific)**: the
classifier is portable, the dispatch table (which model, when to watch) is tuned per
project and toolchain.

#### Scenario: Stateful/object-lifecycle work is dispatched
- **WHEN** a unit involves stateful object lifecycle, cross-subsystem integration,
  or config-critical wiring
- **THEN** it SHALL be assigned the stronger model from turn 1 and supervised, to
  avoid the stall-then-escalate waste (field log §5.10, M3; §3 M6)

#### Scenario: Well-specified pure-logic work is dispatched
- **WHEN** a unit is well-specified logic with a detailed spec and deterministic
  tests
- **THEN** it MAY run on the cheaper model and (preconditions permitting) unattended
  (field log M4/M5)

### Requirement: Classification affects cost, not correctness

The framework SHALL treat the work-class dial as buying *cheaper* correctness, not
*more* correctness. A misclassification MUST NOT be able to produce an incorrect
committed artifact — at worst it stalls and commits nothing — because the
convergence machine (gate + commit-as-truth) remains the correctness guarantee. This
requirement is **methodology (portable)**: the principle that the dial is an
efficiency lever, not a correctness lever, carries to any project.

#### Scenario: A unit is misclassified as pure and left unattended
- **WHEN** stateful work is wrongly run unattended on a cheap model
- **THEN** the worst outcome is a stalled turn with no commit (caught by the stall
  detector), never a bad commit reaching main — cost is paid in clock, not quality

### Requirement: Autonomy is an opt-in mode gated on preconditions

The framework SHALL present unattended execution (the loop runner, container
sandbox, and any fan-out) as an **opt-in deployment mode**, not the default, and only
when ALL four preconditions hold: (1) the work is well-specified, (2) the model tier
is matched from turn 1, (3) the operator is genuinely absent (away-time is real
otherwise-idle wall-clock), and (4) for parallel fan-out, a single unit's build time
dominates its per-unit coordination cost. The framework SHALL record that
unattended operation was, in evidence, *catalytic and narrow-band* — not a general
accelerator. This requirement is **configurable (project-specific)**.

#### Scenario: Preconditions are not all met
- **WHEN** any of the four preconditions is false (e.g. stateful work, or the
  operator is effectively supervising)
- **THEN** the unit SHALL be built supervised-direct; unattended mode is not invoked

#### Scenario: Fan-out is considered for parallel content
- **WHEN** independent content units are candidates for parallel fan-out
- **THEN** fan-out MUST be treated as serial-by-default with opt-in only, and only
  reached for when per-unit build time dominates coordination cost; the M10
  implementation was net-negative at small unit size and is not a turnkey speedup
  (field log §3 M10, §5.13–5.16)

### Requirement: Velocity targets serial latency, not turn throughput

The framework SHALL identify the human-gate cycle (PR → CI → review → fixes →
merge) as the real bottleneck, and direct velocity effort at *serial latency* —
batching clean milestones per PR, auto-merging when the independent reviewer is
clean, and matching model to task type — rather than at parallelizing the loop.
Parallelize the independent units the architecture produces, not the convergence
loop itself. This requirement is **methodology (portable)**.

#### Scenario: An operator tries to go faster by parallelizing the loop
- **WHEN** the impulse is "more containers / more agents on the same milestone"
- **THEN** the framework directs effort instead to the latency moves, because
  systems-layer work shares files and collides; turn throughput was never the
  constraint (field log §10)

### Requirement: Enabling patterns reduce cost of the convergence machine

The framework SHALL document enabling patterns — a pure, framework-free rules core
with a value-driven test seam, and a two-tier context layout (lean always-loaded
file + on-demand depth) — as practices that make the Layer-1 contract cheap and
fast, distinct from the correctness rules themselves. These are **configurable
(project-specific)**: their shape depends on the stack.

#### Scenario: Core logic is made deterministically testable
- **WHEN** the most bug-prone logic is isolated from the framework/runtime
- **THEN** it can be unit-tested without booting the runtime — fast, deterministic,
  strict-typed — lowering the cost of satisfying the spec-first contract

