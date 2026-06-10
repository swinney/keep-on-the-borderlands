# Ralph Harness Kit

A copyable, project-agnostic harness for building software with an LLM coding
agent in a spec-driven loop. It runs the agent one task at a time inside a
sandbox container, uses the **commit graph** as the objective progress signal,
pauses cleanly on usage limits, and halts for human review when it stalls.

This is the **runnable** counterpart to the methodology in
[`../docs/framework/`](../docs/framework/README.md) — specifically the Layer-2
"autonomy wrapper" that framework describes but ships no files for. Read the
framework for *why* the loop is shaped this way; use this kit to *run* it.

## What's here

```
ralph-harness/
  scripts/
    ralph.sh          # the loop runner (config-driven; --once for a single turn)
    ralph-status.sh   # one-shot status digest (works whether or not a loop runs)
    until_reset.py    # usage-limit reset-time math (pure stdlib)
  templates/
    PROMPT.md.template       # the loop contract; fill the {{PLACEHOLDERS}}
    Containerfile.template   # sandbox image; swap one toolchain block
    Makefile.template        # build/login/loop/status driver targets
  example/            # the templates fully resolved for a sample project
  tests/
    run.sh            # runs both suites below
    test_until_reset.py
    test_ralph_runner.sh
  ralph.conf.example  # every project-specific value, documented
  .gitignore          # the lines to copy into your repo's .gitignore
```

The runtime scripts are driven entirely by **configuration**, never edited. Only
the three template files (which can't be sourced at runtime) are filled in by
hand at adoption.

## Adoption

1. **Copy the kit.** Copy this whole `ralph-harness/` directory into your repo
   (it is self-contained — nothing outside it is referenced).
2. **Create your config.** Copy `ralph-harness/ralph.conf.example` to
   `ralph.conf` at your repo root and edit the values (see the reference below).
3. **Fill the templates** (the only files you hand-edit). Resolve every
   `{{PLACEHOLDER}}`, then put the results where the loop expects them:
   - `templates/PROMPT.md.template` → `PROMPT.md` at your repo root.
   - `templates/Containerfile.template` → `Containerfile` at your repo root
     (replace the marked toolchain block with your project's deps + gate tools).
   - `templates/Makefile.template` → `Makefile` at your repo root.
   The [`example/`](example/) directory shows all of these resolved.
4. **Gitignore the state dir.** Copy the lines from `ralph-harness/.gitignore`
   into your repo's `.gitignore` (the loop writes auth tokens and logs under
   `RALPH_STATE_DIR`, default `.ralph/` — these must never be committed).
5. **Add a task list.** Create `tasks.md` at your repo root with
   `- [ ] 1.1 ...` checkbox tasks; the loop works the first unchecked one each turn.
6. **Build the sandbox.** `make build`.
7. **Authenticate once.** `make login` (persists Claude Code auth under the
   state dir so later runs are non-interactive).
8. **Run the loop.** `make loop` (foreground, Ctrl-C to stop), or `make loop-once`
   for a single turn. Watch progress with `make status` or
   `tail -f .ralph/log/turn-*.txt`.

The loop stops when a turn writes a stop reason to `STATUS.md`, after
`RALPH_MAX_STALLS` consecutive no-commit turns, or on Ctrl-C.

You do **not** need the container to try the runner: with `claude` on your PATH
and an authenticated `$HOME/.claude`, `bash ralph-harness/scripts/ralph.sh --once`
runs one turn against your `PROMPT.md`.

## Parameter reference

### `ralph.conf` keys (config; env var of the same name overrides)

| Key | Meaning | Default |
|---|---|---|
| `RALPH_WORKSPACE` | Project dir the loop operates in (bind-mount target in a container) | current dir |
| `RALPH_TASKS` | Task-list file, relative to the workspace | `tasks.md` |
| `RALPH_STATE_DIR` | Runtime state dir (logs, heartbeat, feed, counter); gitignore this | `.ralph` |
| `RALPH_CONF` | Path to the config file to source (env-only; points the scripts elsewhere) | `./ralph.conf` |
| `RALPH_MODEL` | Model id passed to `claude --model` | account default (empty) |
| `RALPH_TURN_TIMEOUT` | Per-turn wall-clock cap, seconds (exceeded → killed, retried) | `1200` |
| `RALPH_MAX_STALLS` | Consecutive no-commit turns before halting for review | `2` |
| `RALPH_LIMIT_POLL` | Fallback wait, seconds, on an unparseable usage-limit reset | `900` |
| `RALPH_POLL_INTERVAL` | Inter-turn sleep in loop mode, seconds | `30` |
| `RALPH_CONTAINER` | Loop container/image name (digest probes it; Makefile builds it) | `ralph-loop` |
| `RALPH_RUNTIME` | Container runtime CLI | `podman` |

### Template placeholders (hand-filled once at adoption)

| Placeholder | File | Meaning |
|---|---|---|
| `{{PROJECT_NAME}}` | PROMPT.md | Human name of the project |
| `{{SPECS_DIR}}` | PROMPT.md | Directory holding the written specs (e.g. `docs/specs`) |
| `{{TESTS_DIR}}` | PROMPT.md | Directory holding the test suites (e.g. `tests`) |
| `{{DECISIONS_DIR}}` | PROMPT.md | Directory for decision records (e.g. `docs/decisions`) |
| `{{GATE_COMMAND}}` | PROMPT.md | Full pre-commit gate, in CI order, as one line |
| `{{BASE_IMAGE}}` | Containerfile | Base container image (e.g. `python:3.12-slim`) |
| `{{TOOLCHAIN_INSTALL}}` | Containerfile | One `RUN` block installing project deps + gate tools |
| `{{CONTAINER_IMAGE}}` | Makefile | Image/container name (match `RALPH_CONTAINER`) |
| `{{RUNTIME}}` | Makefile | Container CLI (match `RALPH_RUNTIME`) |

## Tests

```
bash ralph-harness/tests/run.sh
```

Runs the `until_reset.py` unit tests (pure, via `pytest`) and the `ralph.sh`
behavioural scaffold (git-fixture based, stubs the `claude` binary). Both are
self-contained — they need only `bash`, `git`, `python3` (+ `pytest`), and
`timeout`, not any host project's test configuration.

## Relationship to this repo's live harness (drift note)

This kit is an **extracted, generalized copy** of the live harness that drove the
*Keep on the Borderlands* build — the repo-root `scripts/ralph.sh`,
`scripts/ralph-status.sh`, `scripts/until_reset.py`, `PROMPT.md`, `Containerfile`,
and `Makefile`. Those live files are **not** modified by this kit and continue to
run that project's loop, so **the two copies can drift over time.**

- **For an adopter, this kit (`ralph-harness/`) is canonical.** Copy from here.
- The live files are the battle-tested originals; the kit lifts their hardcoded
  values (`/workspace`, the `kotb-ralph` image, the Evennia toolchain, the
  KOTB-specific prompt) into config and templates, and adds `RALPH_POLL_INTERVAL`.
- **Deliberate portability divergences from the originals** (so a diff isn't a
  surprise): the kit scripts avoid bash-4 associative arrays so they run on
  bash 3.2 (stock macOS), and `scripts/until_reset.py` aliases
  `UTC = timezone.utc` so it works on Python 3.7+ (the live copy uses the 3.11+
  `datetime.UTC`). Behaviour is identical.
- **Synced from the live files at commit `47d4145`** (live harness logic last
  changed in `f454e6b`). To reconcile later, diff `ralph-harness/scripts/` against
  the repo-root `scripts/` from that point forward.

Fan-out / parallel-clone tooling (the project's `scripts/fanout*.sh`) is **not**
included: it is project-specific and unproven, and is deliberately deferred.

## Why this shape (methodology)

See [`../docs/framework/`](../docs/framework/README.md):
- **Layer 1 — convergence machine** (portable): the contract → proof → review
  spine this loop enforces (the gate in `PROMPT.md`, commit-as-proof in `ralph.sh`).
- **Layer 2 — dispatch + deployment** (project-specific): this kit *is* the
  autonomy wrapper — loop runner + container, opt-in and gated.
- **Layer 3 — operator discipline** (unenforceable): the human habits the harness
  can't enforce.
