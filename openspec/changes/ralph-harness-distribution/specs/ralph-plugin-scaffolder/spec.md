## ADDED Requirements

### Requirement: Installable as a self-hosted GitHub marketplace

The harness SHALL ship as a Claude Code plugin whose repo contains a
`.claude-plugin/marketplace.json` and `.claude-plugin/plugin.json`, so a teammate
installs it with `/plugin marketplace add swinney/keep-on-ralphing` followed by
`/plugin install`. It MUST NOT require submission to any public plugin directory.

#### Scenario: Team install from GitHub

- **WHEN** a teammate runs `/plugin marketplace add swinney/keep-on-ralphing` then
  installs the plugin
- **THEN** the `/ralph-init` and `/ralph-status` skills become available, with no
  public-directory step involved

### Requirement: `/ralph-init` scaffolds per-project config from the repo's context

The `/ralph-init` skill SHALL generate a target project's per-project config from
templates bundled in the plugin, filling placeholders from the target repo's own
context where inferable (project name, specs/tests dirs, the gate command from CI
config) and prompting only where it cannot infer. It MUST produce: `ralph.conf`,
a filled `PROMPT.md`, a `tasks.md` starter, a thin `Containerfile` that `FROM`s the
base image, and a thin `Makefile`; and it MUST ensure the state dir is gitignored.

#### Scenario: Scaffolding a fresh project

- **WHEN** `/ralph-init` runs in a project that has no harness config
- **THEN** it writes the per-project config files, leaves the gate command and
  paths reflecting that repo, and reports what it inferred vs. asked

#### Scenario: Templates are the single config source

- **WHEN** the config surface (a placeholder, a default) needs to change
- **THEN** it is edited once in the plugin's bundled templates, and future
  `/ralph-init` runs reflect it — no per-project template copies

### Requirement: A worked example as the golden reference

The plugin repo SHALL include a fully-resolved worked example (config + thin
Containerfile/Makefile for a sample project) that `/ralph-init` and adopters can
diff against. The example's image name, workspace, and gate command MUST be
mutually consistent.

#### Scenario: Example mirrors what /ralph-init emits

- **WHEN** an adopter compares `/ralph-init` output to the worked example
- **THEN** the structure matches and the example's values are internally consistent

### Requirement: Scaffolding does not break the non-interactive path

`/ralph-init` output SHALL keep the project runnable headlessly: the generated
config MUST NOT require interactive input for the loop or container build to start
(beyond the one-time `make login`).

#### Scenario: Generated config runs headless

- **WHEN** the loop is started against `/ralph-init`-generated config after
  `make login`
- **THEN** it runs turns without further interactive prompts
