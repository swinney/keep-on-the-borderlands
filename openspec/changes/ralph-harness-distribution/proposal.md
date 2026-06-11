## Why

The Ralph harness now exists in three forms inside this repo: the live machinery
that drives the KOTB build (`scripts/ralph*.sh`, `scripts/until_reset.py`,
`scripts/fanout*.sh`, root `Containerfile`/`Makefile`/`PROMPT.md`), the extracted
reusable kit (`ralph-harness/`, merged in #38), and the methodology corpus
(`docs/framework/`, `docs/ralph-loop*.md`). All of it lives in a game repo, so a
teammate who wants the harness for *their* project must clone the MUD and copy
files — and every copy drifts (the exact problem #38's README had to confess).

The harness has outgrown its host. It should be its own thing: a single
GitHub-hosted source the team installs once and points at any project. This
change externalizes it into a new repo, **`swinney/keep-on-ralphing`**, turns the
machinery into a podman base image plus a Claude Code plugin, and leaves KOTB as
the harness's *first consumer* — carrying only its per-project config, no
machinery. Scope is deliberately narrow: **Linux + podman, single-arch, no public
marketplace directory, team-shared via GitHub.**

## What Changes

- **New repo `swinney/keep-on-ralphing`** becomes the single home of the harness:
  the base image build context (machinery baked in), the Claude Code plugin
  (`/ralph-init`, `/ralph-status`, bundled templates), the worked example, and the
  methodology docs.
- **Base sandbox image** — `base/Containerfile` `COPY`s the runner machinery
  (`ralph.sh`, `until_reset.py`) to `/usr/local/bin`. Consuming projects write a
  ~6-line `Containerfile` (`FROM keep-on-ralphing-base` + their toolchain). The
  machinery exists in exactly one place; no project copies `scripts/`. Built
  locally via `make build-base` (registry-free; GHCR is a documented later add).
- **Claude Code plugin** (self-hosted marketplace via `marketplace.json` in the
  repo — installable with `/plugin marketplace add swinney/keep-on-ralphing`, no
  directory submission):
  - `/ralph-init` — scaffolds a target repo's per-project config (`ralph.conf`,
    `PROMPT.md`, `tasks.md`, the thin `Containerfile`/`Makefile`) by reading the
    repo, and offers to build the base image.
  - `/ralph-status` — replaces the host-side `ralph-status.sh` shell digest; a
    skill that reads `.ralph/current.json` + `status.jsonl` + `git` and reports.
- **KOTB is migrated to consume the externalized harness** and **all harness
  machinery + methodology is removed from KOTB.** KOTB keeps only the thin
  per-project config needed to keep its own loop running (it is loop-driven via
  the pending `rpg-and-runtime-completion`), plus its build retrospective.
  **BREAKING** for anyone currently running `make loop` from KOTB: the workflow
  becomes "install the plugin, `/ralph-init`, build the base" instead of in-repo
  scripts.
- **Migration ordering guarantees KOTB never loses the ability to loop**: stand up
  `keep-on-ralphing` and prove KOTB can consume it (base builds, loop runs green)
  *before* deleting anything from KOTB.

## Capabilities

### New Capabilities
- `ralph-base-image`: the podman base sandbox image — generic OS/Node/Claude-Code
  layer + the runner machinery baked to PATH, a single marked toolchain block for
  consumers, UID/GID-matched user, local `make build-base`, single-arch Linux.
- `ralph-plugin-scaffolder`: the Claude Code plugin + `/ralph-init` skill that
  scaffolds a target repo's per-project config from bundled templates and the
  repo's own context, plus the self-hosted `marketplace.json` install path.
- `ralph-status-skill`: the `/ralph-status` skill that reports loop status from the
  state outputs (`current.json`, `status.jsonl`), `STATUS.md`, and `git`, working
  whether or not a loop is currently running.

### Modified Capabilities
<!-- None. The kit's three capabilities (harness-loop-runner,
     harness-config-templates, harness-kit-packaging) describe the in-KOTB kit;
     this change relocates and re-packages that surface into the new repo rather
     than changing its behavioral requirements. The relocation is handled in
     tasks/migration, not as spec deltas. -->

## Impact

- **Two repos.** Most new artifacts land in `swinney/keep-on-ralphing` (created by
  this change). The change itself is authored in KOTB's `openspec/` (where the
  decision history lives); tasks call out which steps run in which repo.
- **KOTB deletions** (machinery + methodology leave): `scripts/ralph*.sh`,
  `scripts/until_reset.py`, `scripts/fanout*.sh`, `scripts/m10-tribes.txt`,
  `ralph-harness/`, root `Containerfile`/`Makefile`/`PROMPT.md` (the generic ones),
  `docs/ralph-loop.md`, `docs/framework/`, `docs/ralph-loop-evaluation.md`,
  `docs/specs/fanout-harness.md`. The field log `docs/ralph-loop-experiment.md`
  moves too (it is the harness's evidence base) — the single most debatable move;
  see design.
- **KOTB retains** only consumer config: `ralph.conf`, its filled `PROMPT.md`,
  `tasks.md`, `STATUS.md`, a thin `Containerfile`/`Makefile`. `Containerfile.runtime`
  + `compose.yaml` (game serving — not harness) are untouched.
- **CLAUDE.md** §5/§6/§7 + the cold-start map are rewritten to describe consuming
  `keep-on-ralphing` instead of in-repo harness; auto-memories referencing harness
  paths (`experiment-log-upkeep`, framework pointers) are updated.
- No change to the game, its tests, or CI's quality gate.
