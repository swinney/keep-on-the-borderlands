## Context

The harness that drove this build is proven across eleven milestones but lives
inline, with project-specific values interleaved into generic machinery:

- `scripts/ralph.sh` (246 lines) — the loop. Already config-friendly: every knob
  is an `RALPH_*` env var (`RALPH_MODEL`, `RALPH_TURN_TIMEOUT`, `RALPH_MAX_STALLS`,
  `RALPH_LIMIT_POLL`, `RALPH_TASKS`, `RALPH_STATE_DIR`). The only hard couplings
  are a literal `cd /workspace` and prose comments naming the container.
- `scripts/until_reset.py` (98 lines) — pure stdlib, fully project-agnostic.
- `scripts/ralph-status.sh` (63 lines) — hardcodes the `kotb-ralph` container
  name and `.ralph/` paths.
- `PROMPT.md` (root) — the loop contract, but written for KOTB/Evennia (specs
  path, the `ruff → mypy → pytest` gate, Evennia-contrib conventions).
- `Containerfile` / `Makefile` — sandbox + driver. The Containerfile bakes the
  Evennia/Django toolchain; the Makefile hardcodes `IMAGE := kotb-ralph` and
  podman invocations.

The methodology is already distilled to prose in `docs/framework/` (archived
`ralph-framework-v1`, three capability specs). That playbook explicitly names a
**Layer-2 autonomy wrapper** — "loop runner · container · fan-out" — as the
project-specific part you re-tune, but it ships *no files*. This change is the
missing runnable counterpart.

## Goals / Non-Goals

**Goals:**
- Extract the harness into a self-contained, copyable `ralph-harness/` directory.
- Concentrate every project-specific value into one sourced `ralph.conf`; keep the
  runner logic literal-free.
- Ship the three things that *can't* be pure config (the prompt contract, the
  container toolchain, the Makefile driver) as templates with a closed, documented
  placeholder set plus a worked example.
- Leave the live, running harness untouched so `rpg-and-runtime-completion` keeps
  looping.

**Non-Goals:**
- No fan-out tooling (`fanout*.sh`, `m10-tribes.txt`) — M10-specific and unproven
  (`loop-speedup-strategy`). Deferred, with a note in the README that it exists.
- No code generator / scaffolding CLI — adoption is copy + edit one config + fill
  documented placeholders. A generator is more surface than the payoff at N=1.
- No change to the methodology docs beyond adding a cross-link pointer.
- Not making the live project consume the kit yet (that invites mid-loop drift on
  an active build); v1 is extraction only.

## Decisions

### D1: Sourced `ralph.conf`, not codegen, for the runtime scripts

The runner and digest **source** a `ralph.conf` (shell `KEY=VALUE`) at startup,
layered as: env var > `ralph.conf` > built-in default. The runner is already
env-var-driven, so this is a thin addition (source the file, then apply defaults
with `${VAR:-default}`), and config stays separate from code — no generated files
to regenerate when logic changes.
- *Alternative — a templating/codegen step that bakes values into script copies:*
  rejected. It creates generated artifacts that drift from their source and adds a
  build step to what is otherwise "copy and run."

### D2: Templates only for the three files config can't cover

`PROMPT.md`, `Containerfile`, and `Makefile` are not sourced at runtime, so config
can't parameterize them. They ship as `*.template` with a closed, documented
placeholder set (e.g. `{{PROJECT_NAME}}`, `{{SPECS_DIR}}`, `{{GATE_COMMAND}}`,
`{{CONTAINER_IMAGE}}`, `{{TOOLCHAIN_INSTALL}}`) the adopter fills by hand, plus a
fully-resolved worked example so the blanks are never the only reference.
- *Alternative — generate these from `ralph.conf` too:* rejected for v1 (see D1);
  hand-editing three files once at adoption is cheaper than owning a generator.

### D3: Extract a generalized copy; do not refactor the live files

The kit is a *copy* of the live scripts with the couplings lifted out, committed
under `ralph-harness/`. The live `scripts/`, `PROMPT.md`, etc. are not modified.
- *Why:* the loop is actively running `rpg-and-runtime-completion`. Refactoring the
  live runner to source the new config mid-build risks halting a working loop for
  zero user-visible gain. The cost is a documented drift risk (D6).
- *Alternative — make the live files the single source and have the project consume
  the kit:* the right end-state, but sequenced *after* this change, not during it.

### D4: `until_reset.py` copied verbatim

It is already pure-stdlib and parameter-free. The kit copies it unchanged; its
unit tests (deterministic via injectable `now`) come along so the helper stays
green in any adopter repo.

### D5: Container runtime stays podman-by-default, but named via config

The Makefile template keeps podman as the default (matching ADR-0001 and the
rootless-UID-mapping rationale) but reads the image name and workspace from config.
The runtime binary is left as a documented assumption rather than abstracted into a
`$RUNTIME` shim — docker/podman CLI compatibility is close but not total, and
faking full portability we haven't tested would be dishonest at N=1.

### D6: Drift between kit and live files is disclosed, not engineered away

Because D3 keeps two copies, the README states plainly: the kit is a generalized
copy, the two can drift, and the kit is canonical for an adopter. A short
"last synced from commit `<sha>`" line in the README gives a manual reconciliation
anchor. This is the honest N=1 position rather than pretending one source.

## Risks / Trade-offs

- **Two copies of the runner drift apart.** → Disclosed in the README with a
  "synced-from" SHA; the live file remains the battle-tested one, the kit the
  adoptable one. A future change can collapse them once this build's loop ends.
- **Placeholder set is incomplete and a hidden literal ships.** → The
  packaging spec requires the parameter reference to be *complete* (every consumed
  placeholder/key listed, nothing extra); the worked example exercises every
  placeholder, surfacing any that were missed.
- **`ralph.conf` sourcing executes shell.** A malicious config could run code. →
  Same trust model as the existing scripts (you run the harness on your own repo);
  documented, not sandboxed. No remote/untrusted config path exists.
- **Container portability overclaimed.** → D5 keeps podman as the stated default
  and documents docker as "likely works, untested," rather than shipping an
  unverified abstraction.
- **Adopter forgets to gitignore the state dir** and commits auth/logs. → The
  README adoption flow makes gitignoring `RALPH_STATE_DIR` an explicit numbered
  step, and the example `.gitignore` snippet ships in the kit.

## Migration Plan

Purely additive: new files under `ralph-harness/`. No runtime file changes, so no
rollback concern for the live loop — deleting the directory fully reverts. The
methodology docs gain a one-line cross-link pointer (reversible). Sequencing within
this change follows the spec order: runner machinery first (it has the unit tests),
then config + templates, then packaging/README, with the worked example and the
cross-link last so they reflect the finished surface.

## Open Questions

- Should the kit eventually become the single source the live project consumes
  (collapsing the two copies)? Default: defer to a follow-up change after this
  build's loop concludes; not in scope here.
- Do we ship the fan-out scripts as an "advanced/unproven" extra later, or leave
  them out entirely? Default: leave out of v1; revisit only if a second project
  actually needs parallel fan-out.
