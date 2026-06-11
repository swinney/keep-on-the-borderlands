# harness-config-templates Specification

## Purpose
TBD - created by archiving change ralph-harness-kit. Update Purpose after archive.
## Requirements
### Requirement: Answer-once config contract

The kit SHALL define a single `ralph.conf` file as the one place an adopter sets
project-specific values. It MUST ship as `ralph.conf.example` with every
supported key present, documented inline, and set to a safe default or an obvious
placeholder. The supported keys MUST at minimum cover: workspace path, tasks-file
path, state directory, container image name, model id, per-turn timeout,
max-stalls, and limit-poll fallback.

#### Scenario: Example config enumerates every key

- **WHEN** an adopter opens `ralph.conf.example`
- **THEN** every `RALPH_*` value the runner and digest read is present with an
  inline comment describing it, so no parameter is discoverable only by reading
  the scripts

#### Scenario: Copy-and-edit adoption

- **WHEN** an adopter copies `ralph.conf.example` to `ralph.conf` and edits the
  values for their project
- **THEN** the runner and digest pick up those values with no edit to any script

### Requirement: PROMPT.md template with closed placeholder set

The kit SHALL provide a `PROMPT.md` template carrying the portable loop contract
(one task per invocation; spec-then-test-then-implement ordering; run the full
gate in CI order before committing; never commit red; the documented stop
conditions; the no-`Co-Authored-By` rule). Project-specific content MUST appear
only as a closed, documented set of placeholders — at minimum the project name,
the specs directory, and the gate command sequence.

#### Scenario: Placeholders are documented and finite

- **WHEN** an adopter reads the template and its accompanying placeholder
  reference
- **THEN** every placeholder is listed with its meaning, and the template contains
  no project-specific literal outside that documented set

#### Scenario: Portable contract survives templating

- **WHEN** the placeholders are filled in
- **THEN** the resulting `PROMPT.md` still expresses the full stop conditions, the
  commit-gate ordering, and the no-attribution rule unchanged

### Requirement: Container and Makefile templates

The kit SHALL provide a `Containerfile` template and a `Makefile` template that
realize the sandbox and its driver targets. The Containerfile MUST isolate the
project toolchain install into a single clearly-marked block an adopter replaces,
while keeping the generic base (OS tools, Node, the Claude Code install, the
UID/GID-matched non-root user) intact. The Makefile MUST expose the driver
targets (`build`, `login`, `loop`, `loop-once`, `shell`, `status`, `clean`) with
the image name and workspace sourced from configuration, not hardcoded.

#### Scenario: Toolchain block is the only Containerfile edit

- **WHEN** an adopter swaps the marked toolchain-install block for their project's
  dependencies
- **THEN** the base image, Claude Code install, and UID/GID-matched user require
  no further edits to build a working sandbox

#### Scenario: Makefile targets are config-driven

- **WHEN** the image name or workspace is changed in configuration
- **THEN** the Makefile targets use the new values without edits to the target
  recipes

### Requirement: Worked example

The kit SHALL include a filled-in worked example (a populated `ralph.conf` and the
templates with placeholders resolved for a sample project) so an adopter sees a
concrete, working configuration alongside the blanks.

#### Scenario: Example is concrete and consistent

- **WHEN** an adopter compares the worked example to the blank templates
- **THEN** the example shows real values for every placeholder and config key, and
  those values are mutually consistent (the image name, workspace, and gate
  command agree across the example files)

