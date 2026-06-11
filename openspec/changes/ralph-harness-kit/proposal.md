## Why

The Ralph Loop harness that drove this build — the loop runner, the usage-limit
pause logic, the status digest, the `PROMPT.md` contract, and the container +
Makefile driver — lives inline in this repo (`scripts/`, root `PROMPT.md`,
`Containerfile`, `Makefile`) with project-specific values (the `kotb-ralph`
image name, a hardcoded `/workspace`, the Evennia toolchain, KOTB conventions)
baked into otherwise-generic machinery. Reusing it on the next project today
means hand-copying files and hunting for the lines to change. The methodology is
already distilled to prose in `docs/framework/` (the archived `ralph-framework-v1`);
what is missing is the **runnable** counterpart — the Layer-2 "autonomy wrapper"
the framework names but does not ship as files. This change extracts that wrapper
into a self-contained, parameterized kit a new repo can adopt by editing one
config file.

## What Changes

- Add a self-contained `ralph-harness/` kit directory at the repo root, holding
  the generalized, project-agnostic harness.
- **Separate generic machinery from answer-once config.** The loop runner,
  usage-limit math, and status digest become driven entirely by a single sourced
  config file (`ralph.conf`) plus the existing `RALPH_*` env-var overrides — no
  project name, path, or container name hardcoded in the logic.
- Ship `until_reset.py` verbatim (already pure-stdlib and project-agnostic).
- Provide `PROMPT.md`, `Containerfile`, and `Makefile` as **templates** with a
  documented, finite set of placeholders (project name, specs dir, gate command,
  container image, toolchain install block) and a worked example filled in.
- Add a kit `README.md`: the adoption flow, the full parameter reference, and the
  no-drift relationship to the live project files and to `docs/framework/`.
- **No change to the running loop.** The live `scripts/`, `PROMPT.md`,
  `Containerfile`, and `Makefile` stay exactly as they are so the in-progress
  `rpg-and-runtime-completion` loop keeps running; the kit is an extracted,
  generalized copy, and the drift risk between the two is documented.
- **Out of scope (v1):** the fan-out tooling (`scripts/fanout*.sh`,
  `m10-tribes.txt`) is M10-specific and unproven (see `loop-speedup-strategy`);
  it is deliberately deferred, not extracted.

## Capabilities

### New Capabilities
- `harness-loop-runner`: the generic, config-driven loop runner — turn execution
  with per-turn timeout, the commit-as-progress signal, the consecutive-stall
  halt, the usage-limit pause-and-replay (via `until_reset.py`), the gitignored
  state outputs (`current.json` heartbeat, `status.jsonl` feed, turn counter),
  and the one-shot status digest. Parameterized, with nothing project-specific in
  the logic.
- `harness-config-templates`: the answer-once config contract (`ralph.conf`) and
  the three editable templates (`PROMPT.md`, `Containerfile`, `Makefile`) with a
  closed set of documented placeholders and a worked example.
- `harness-kit-packaging`: the self-contained `ralph-harness/` layout, the
  adoption/install flow into a target repo, the kit README + parameter reference,
  and the documented no-drift relationship to the live project files and to the
  `docs/framework/` methodology.

### Modified Capabilities
<!-- None. The methodology specs (convergence-machine, work-dispatch,
     operator-discipline) keep their requirements unchanged; this kit is the
     concrete, runnable realization of work-dispatch's autonomy wrapper. -->

## Impact

- **New files only** under `ralph-harness/`. No existing runtime file is modified,
  so the active loop and CI are unaffected.
- Depends on the same external tools the current harness assumes (bash, git,
  `python3` for the helpers, and a container runtime — podman by default — on the
  adopter's host). No new project dependencies.
- Cross-references `docs/framework/` (methodology) and `docs/ralph-loop.md`
  (project ops); those docs get a pointer to the kit but no structural change.
