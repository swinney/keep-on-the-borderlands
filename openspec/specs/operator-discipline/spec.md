# operator-discipline Specification

## Purpose
TBD - created by archiving change ralph-framework-v1. Update Purpose after archive.
## Requirements
### Requirement: Operator discipline is mandatory despite being unenforceable

The framework SHALL treat operator discipline as a first-class, mandatory layer —
not an appendix — while acknowledging it is the one layer the gate structurally
CANNOT enforce. The operator (the session that launches, kills, triages, theorizes,
and merges) is the only role with no gate: operator actions are not commits, so the
commit-graph instrument is blind to them. Output quality therefore MUST NOT be taken
as evidence of operator discipline; the two are decoupled ("resilience masks
sloppiness"). This requirement is **methodology (portable)**.

#### Scenario: A session produces clean output through heavy thrash
- **WHEN** a session ships zero red commits and loses no work, but did so via runaway
  processes, brute-force loops, or wrong theories
- **THEN** the clean commit graph MUST NOT be read as a well-run session; operator
  discipline requires a separate signal (field log §5.13–5.16, M10)

### Requirement: Epistemic discipline — do not act on unverified belief

The operator SHALL do cheap analysis before expensive action and SHALL NOT construct
causal narratives about external-system behavior from indirect signals. For an
intermittent failure, the operator MUST first ask: is it possible from the code? is
it an infra artifact? does it matter? — before any reproduction loop. For claims
about systems the operator does not control, the operator MUST state uncertainty and
defer to ground truth (the user's direct knowledge). This requirement is
**methodology (portable)**.

#### Scenario: An intermittent test failure is observed once
- **WHEN** a test fails once and the impulse is to re-run it many times
- **THEN** the operator MUST run the possible/infra/worth-it triage first, and state
  the conclusion before spending compute (field log §5.14)

#### Scenario: External-system behavior needs explaining
- **WHEN** the operator is tempted to infer *why* an external system behaved a
  certain way from timestamps or partial output
- **THEN** the operator MUST present what is verified, flag what is inferred, and
  defer to the user's ground truth rather than asserting a tidy narrative (§5.16)

### Requirement: Procedural discipline — manage the environment cleanly

The operator SHALL run long jobs only through tracked, named, killable-by-id
mechanisms (never a bare background `&`), SHALL verify cleanup with a broad process
check rather than a narrow name-prefix match, SHALL place scope/constraints in the
prompt rather than relying on filesystem layout, and SHALL run one orchestrator at a
time. This requirement is **methodology (portable)**; the specific commands are
project/toolchain-specific.

#### Scenario: A long job is backgrounded
- **WHEN** the operator needs to run a long-lived job
- **THEN** it MUST be named and tracked so it is killable by id, and verified clean
  with a broad check — auto-named detached jobs that slip a name-prefix grep are a
  known failure (field log §5.15)

#### Scenario: Parallel work is scoped
- **WHEN** parallel units are launched with their own directories
- **THEN** the scope constraint MUST also be in each unit's prompt, because
  infrastructure isolation is not intent isolation — a loop reads the whole repo and
  will over-deliver if only the filesystem fences it (field log §5.13)

### Requirement: Teeth-substitutes for the missing gate

Because no gate can block operator failures, the framework SHALL give Layer 3 two
substitutes: (a) **instrumentation** that surfaces non-commit state (running
processes, resource use, per-turn heartbeat/log, the operator's stated reasoning) so
thrash becomes visible; and (b) **pre-action checklists** triggered at the three
high-risk moments — before backgrounding a job, before reproducing a failure, and
before asserting a causal "why". This requirement is **methodology (portable)**.

#### Scenario: A high-risk operator action is about to happen
- **WHEN** the operator is about to background a job, reproduce a failure, or assert
  why an external system behaved as it did
- **THEN** the corresponding pre-action checklist MUST be applied first, since this
  is the only available substitute for a gate the harness cannot provide

#### Scenario: The operator role is automated
- **WHEN** the operator is itself an agent (supervised-direct or higher autonomy)
- **THEN** the discipline MUST be encoded as explicit constraints and instrumentation
  rather than relying on a human to remember, because an agent-operator has the same
  failure modes with less self-awareness

