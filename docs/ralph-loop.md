# Ralph Loop Strategy & Container Operations

Relocated from `CLAUDE.md` §5 and §6 to keep the always-loaded project memory
lean. This is operational reference, read on demand — not every session. The
locked patterns it depends on live in `CLAUDE.md` §3 (Architectural Patterns).

---

## 1. What a Ralph Loop Is

`while true; do claude < PROMPT.md; done` — Geoffrey Huntley's pattern of
running Claude Code unattended against a stable prompt and a living task
list. The cleverness is in the prompt and the surrounding scaffolding.

## 2. Phase Order

1. **Phase 0 — Generate specs:** Feed the OpenSpec prompt
   (`keep-on-borderlands-openspec-prompt.md`) to OpenSpec (or to Claude Code
   as a one-shot). Commit all deliverables. The loop needs specs to converge
   against. **(Complete — see `STATUS.md`.)**
2. **Phase 1 — Bootstrap the repo manually.** Don't make the loop do
   this. Set up: `evennia --init mygame`, git init, ruff/mypy/pytest
   strict, CI workflow running all three, pre-commit hook, `.claude/`
   config, empty `tasks.md` and `STATUS.md`.
3. **Phase 2 — Generate `tasks.md`** from the phased build plan
   (`docs/build-plan.md`). Each task is one Claude Code session of work
   (~spec → tests → implementation for one subsystem slice). Roughly
   80–150 tasks total. Checkboxes so progress is grep-able.
4. **Phase 3 — Write PROMPT.md** (template below).
5. **Phase 4 — Run the loop** in a tmux session.
6. **Phase 5 — Review every few hours** or whenever STATUS.md appears.
   Read commits, skim diffs, check `questions.md`, update specs/tasks,
   restart.

## 3. Build Order (for Ralph-friendliness)

Maximize early integration to surface architectural bugs before they
compound (the authoritative, milestone-mapped version is `docs/build-plan.md`):

1. Repo scaffolding tasks
2. Core combat (smallest testable system)
3. Faction state machine
4. Henchmen
5. Repop and seasonal reset
6. Keep zone
7. Wilderness zone
8. **One cave (kobolds) end-to-end as a vertical slice** — critical;
   surfaces every integration bug before you've built nine more caves
   the same way
9. Remaining caves
10. Shrine
11. Disguised Priest
12. Quest catalog
13. Polish

## 4. PROMPT.md Template (Drop at Repo Root in Phase 1)

```markdown
# Ralph Loop: Keep on the Borderlands MUD

You are building this project iteratively. Each invocation, do ONE task.

## Workflow
1. Read /docs/specs/ to understand the architecture
2. Read /tasks.md and pick the first unchecked task
3. If the task requires a spec that doesn't exist, write the spec first
   in /docs/specs/<system>.md and stop. Mark task progress, commit, exit.
4. If the spec exists but tests don't, write the test suite in
   /tests/<system>/ derived from the spec. Stop. Commit. Exit.
5. If tests exist but fail or are missing implementation, implement
   until all tests pass. Then commit. Exit.
6. Before any commit, run the FULL gate in CI order and fix any failure
   before committing (do not commit red):
   `ruff format .` → `ruff check .` → `mypy` → `pytest`
   CI runs `ruff format --check`, so you must actually FORMAT (not just
   check) — a correctly-typed, passing-tests commit still fails CI if it
   is unformatted.
7. Mark the task complete in /tasks.md if and only if the full
   spec→test→implementation cycle for it is done and green.

## Conventions
- Evennia contribs preferred over custom code; document choices in
  /docs/decisions/
- Type hints everywhere, mypy strict
- One subsystem per commit; commit messages reference the task
- Never modify another subsystem's tests to make your code pass

## Stop conditions
- If /tasks.md is fully checked, write "RALPH: project complete"
  to /STATUS.md and exit
- If you encounter a decision not covered by specs, write the
  question to /docs/questions.md and exit without committing code
- If tests have been red for 3 consecutive commits on the same task,
  write to /STATUS.md and exit for human review

## Important
- Do not invent requirements not in the specs
- Do not skip the spec or test phase to get to implementation faster
- Do not modify /docs/specs/ to match your implementation; modify
  the implementation to match the spec, or escalate via /docs/questions.md
```

## 5. Loop Runner Script

The canonical implementation lives at `scripts/ralph.sh`. Reference sketch:

```bash
#!/usr/bin/env bash
set -u
while true; do
  claude -p --dangerously-skip-permissions < PROMPT.md
  sleep 30
  if [ -f STATUS.md ]; then
    echo "STATUS.md appeared:"
    cat STATUS.md
    break
  fi
done
```

Run in tmux, expect to babysit periodically.

## 6. Operational Tips (Hard-Earned)

- **Use a worktree or dedicated branch.** Be able to nuke loop output
  without losing bootstrap. `git worktree add ../mud-ralph ralph-branch`.
- **Hard quality gates are the safety net.** Strict mypy, ruff, real
  tests. If CI takes >60s, the loop will outrun your ability to review.
- **Token cost is real.** Set a budget, monitor in the Anthropic
  console, use prompt caching (keep spec files at stable paths so
  they cache).
- **"Stuck on red" stop condition is the most important.** Without
  it, the loop spends hours and hundreds of dollars thrashing on a
  test it can't pass. The 3-commits-red rule forces intervention.
- **Use a verification subagent on gnarly subsystems** (faction state
  machine, seasonal reset, rotating Priest). Have the main loop spawn
  a subagent that reviews implementation against spec independently.
- **The loop is a builder, not an architect.** If `questions.md` grows
  fast, the specs are too thin — stop, expand, restart.

---

## 7. Container Setup (Linux Host)

Run the Ralph Loop inside Podman (runtime decision and rationale: ADR
`docs/decisions/0001-container-runtime.md`) so `--dangerously-skip-permissions`
is bounded. The build artifacts are real files: `Containerfile`, `Makefile`.
The scaffolding view is `docs/specs/scaffolding.md` §4.

**Linux-specific advantages:** containers run natively at near-host speed (no
`podman machine` / Docker Desktop VM); rootless Podman works out of the box;
direct bind mounts (no file-sharing penalty).

### Architecture: Hybrid

- **Interactive dev on host:** Edit files in your IDE, run quick smoke tests
  directly (host env via uv — ADR 0003).
- **Ralph Loop inside container** with `--dangerously-skip-permissions`. The
  container has only the project directory mounted and outbound network for
  `pip` / `git push` / Claude API.

### Containerfile (Sketch — canonical version is the real `Containerfile`)

```dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl tmux ca-certificates build-essential \
 && rm -rf /var/lib/apt/lists/*

# Install Claude Code (verify exact install command at build time)
RUN curl -fsSL https://claude.ai/install.sh | sh    # placeholder — verify

# Project tools
RUN pip install --no-cache-dir \
    evennia \
    pytest pytest-django pytest-cov \
    mypy ruff \
    pre-commit

WORKDIR /workspace
CMD ["bash"]
```

### Run Command

```bash
podman run --rm -it \
  --name kotb-ralph \
  -v ~/Projects/keep-on-borderlands:/workspace:Z \
  -e ANTHROPIC_API_KEY \
  kotb-ralph:latest \
  bash -c 'cd /workspace && ./scripts/ralph.sh'
```

The `:Z` SELinux relabel is fine on Fedora/RHEL; drop it on Debian/Ubuntu and
Arch (no SELinux — see ADR 0001). In practice, prefer the `make` targets
(`make build` / `make login` / `make loop`).

### Network Hardening (Optional, Recommended Later)

Once the loop is stable, restrict outbound network to just the Claude API
endpoint and your git remote. Use `--network` with a custom Podman network or
run behind a transparent proxy. Not v1, but worth knowing.

### Fan-out for the Content Layer (M10+)

The content layer (cave tribes) is embarrassingly parallel — each tribe touches
zero files another tribe touches. The fan-out harness runs ≤ N tribe loops
concurrently in separate local clones + containers and opens a per-tribe PR
when each loop hits its gate.

Full design rationale: `docs/specs/fanout-harness.md`.

**Make targets:**

| Target | Action |
|---|---|
| `make fanout` | Launch M10 tribe fan-out (clones, branches, pool of 2, Sonnet) |
| `make fanout-dry` | Print the full plan — clones, branches, task files, launch commands — without running anything |
| `make fanout-status` | Aggregate turn / state / last-commit digest across all active tribe clones |
| `make fanout-land` | Merge tribe PRs that are CI-green + have no Copilot inline comments |

**Model**: Sonnet on each tribe loop (content/replication); Opus on the serial
integration task (minotaur maze + cross-faction wiring) that follows all merges.

**Isolation model**: one local `git clone` per tribe under `../kotb-wt/m10-<tribe>/`,
origin reset to the GitHub remote so `git push` and PRs target GitHub. The
canonical `tasks.md` is never edited by a tribe loop — each clone gets a
scoped `.ralph/tribe-tasks.md` instead.
