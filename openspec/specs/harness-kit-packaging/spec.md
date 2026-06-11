# harness-kit-packaging Specification

## Purpose
TBD - created by archiving change ralph-harness-kit. Update Purpose after archive.
## Requirements
### Requirement: Self-contained kit directory

The kit SHALL live under a single self-contained `ralph-harness/` directory that
an adopter can copy wholesale into a new repository. It MUST NOT import from or
depend on any path outside that directory, so copying the folder is sufficient to
carry the harness.

#### Scenario: Folder copy is sufficient

- **WHEN** the `ralph-harness/` directory is copied into a fresh repository
- **THEN** no referenced file resolves to a path outside the copied directory, and
  the runner, helper, digest, templates, config example, and README are all
  present

### Requirement: Adoption flow

The kit README SHALL document the end-to-end adoption flow as ordered steps: copy
the directory, copy `ralph.conf.example` to `ralph.conf` and edit it, fill the
`PROMPT.md`/`Containerfile`/`Makefile` placeholders, gitignore the state
directory, build the image, authenticate once, then run the loop. Each step MUST
name the exact file or command involved.

#### Scenario: A new adopter can follow the steps unaided

- **WHEN** someone with the kit and no prior context follows the README steps in
  order
- **THEN** they reach a runnable loop without needing to read the script internals
  to discover a required step

### Requirement: Parameter reference

The kit README SHALL include a single table of every adopter-settable parameter —
each `ralph.conf` key and each template placeholder — giving its name, meaning,
and default or example value. The reference MUST be complete: no parameter the
runner, digest, or templates consume may be absent from it.

#### Scenario: Reference matches the shipped surface

- **WHEN** the parameter reference is checked against the config example and the
  template placeholders
- **THEN** every key and placeholder present in those files appears in the table,
  and the table lists no parameter that does not exist

### Requirement: Documented relationship to live files and methodology

The kit README SHALL state that the kit is an extracted, generalized copy of this
repo's live `scripts/`, `PROMPT.md`, `Containerfile`, and `Makefile`, that the two
can drift, and which is canonical for an adopter (the kit). It MUST link to
`docs/framework/` as the methodology the kit operationalizes, and `docs/framework/`
MUST gain a pointer back to the kit as the runnable Layer-2 autonomy wrapper.

#### Scenario: Drift is disclosed, not hidden

- **WHEN** an adopter reads the kit README
- **THEN** it tells them the kit is a generalized copy of the live project files,
  that drift is possible, and that the kit is the canonical source for adoption

#### Scenario: Methodology and runtime cross-link

- **WHEN** a reader is in `docs/framework/`
- **THEN** they find a pointer to `ralph-harness/` as the runnable wrapper, and the
  kit README points back to the framework for the why

