# convergence-machine Specification

## Purpose
TBD - created by archiving change ralph-framework-v1. Update Purpose after archive.
## Requirements
### Requirement: Spec-first contract

The framework SHALL forbid implementation of any unit of work before a written
spec exists and a test derived from that spec exists and fails. The test is the
definition of "done"; the spec is the contract the implementation MUST NOT silently
drift from. This requirement is **methodology (portable)**.

#### Scenario: Work begins without a spec
- **WHEN** a task is picked whose subsystem has no spec in the spec corpus
- **THEN** the operator/agent MUST write the spec first (or escalate) and MUST NOT
  write implementation code in the same step

#### Scenario: Test precedes implementation
- **WHEN** a spec exists but no derived test exists
- **THEN** the failing test suite MUST be authored from the spec's scenarios before
  any implementation, so "done" is defined before it is pursued

### Requirement: Commit as the unit of verified progress

The framework SHALL treat a commit as the only proof that real, gated work
occurred. The local gate MUST mirror the authority gate (CI) exactly and in the
same order; the agent MUST be unable to commit a failing gate ("cannot commit
red"). Nothing uncommitted SHALL be trusted as progress. This requirement is
**methodology (portable)**.

#### Scenario: Local gate diverges from CI
- **WHEN** the local pre-commit gate omits or reorders a check that CI runs (e.g.
  formatter-check)
- **THEN** this is a defect to fix — the gate MUST be made byte-identical to CI, so
  a locally-green commit cannot go CI-red (field log §5.1)

#### Scenario: A turn is killed before committing
- **WHEN** an unattended or supervised turn is interrupted (timeout, outage, reboot)
  with a clean-but-uncommitted working tree
- **THEN** no progress is assumed; recovery re-runs the gate and either commits the
  surviving work or retries the task — killed turns cost only clock, never work
  (field log §5.8, M8/M9)

### Requirement: Independent review as an orthogonal pillar

The framework SHALL require an independent reviewer with no shared mental model,
before merge, on every code change. Review is **assumption-challenging** and
verifies a failure class (the "wired-wrong" class) that assumption-preserving checks
(tests, type-checking, lint) structurally cannot catch; it is not a finer filter of
the same kind and MUST NOT be substituted by more tests. The reviewer SHALL be given
the full artifact and ground-truth external state, but SHALL be withheld the
author's intent/rationale. This requirement is **methodology (portable)**.

#### Scenario: Tests encode the same wrong assumption as the code
- **WHEN** an implementation and its tests share an incorrect premise (e.g. a field
  treated as an enum that the system actually stores as a string)
- **THEN** all tests pass while the behavior is wrong, and only an independent
  reviewer operating from a different prior surfaces it (field log §5.9, M3)

#### Scenario: A clean review must not gate latency
- **WHEN** the independent reviewer returns zero findings and CI is green
- **THEN** the change MAY auto-merge without a human round-trip; review blocks only
  when a finding needs judgment (reconciles review-as-pillar with the human-gate
  cycle being the real bottleneck)

#### Scenario: Reviewer makes a claim about unseen external state
- **WHEN** the reviewer asserts a failure it cannot observe from the artifact (e.g.
  "this fails CI" without CI access)
- **THEN** the claim MUST be verified against ground truth before being applied;
  external-state false positives are the reviewer's own failure class

### Requirement: Guard — do not invent the contract

When the spec is silent on a decision, the agent SHALL escalate to the human
(a questions channel) rather than hallucinate a requirement. The agent is a builder,
not an architect. This requirement is **methodology (portable)**.

#### Scenario: A decision is not covered by the spec
- **WHEN** implementation requires a choice the spec does not specify
- **THEN** the agent MUST record the question and stop, rather than invent and
  encode an unauthorized requirement

### Requirement: Guard — do not game the verification

The agent SHALL change the implementation to satisfy the verification, never the
verification to pass the implementation. It MUST NOT weaken or edit another unit's
tests, the gate, or the spec to turn red green. This is what keeps "cannot commit
red" from being hollow. This requirement is **methodology (portable)**.

#### Scenario: A test blocks a commit
- **WHEN** a failing test stands between the agent and a green gate
- **THEN** the agent MUST fix the implementation (or escalate a genuine spec error),
  and MUST NOT modify the test or spec to make the failure disappear

