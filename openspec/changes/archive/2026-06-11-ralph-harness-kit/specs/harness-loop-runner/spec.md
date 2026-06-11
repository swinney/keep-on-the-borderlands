## ADDED Requirements

### Requirement: Config-driven, project-agnostic runner

The loop runner SHALL contain no project-specific literal (project name,
workspace path, container name, gate command). Every such value MUST come from a
sourced config file (`ralph.conf`) or an `RALPH_*` environment variable, with the
env var taking precedence over the config file, and the config file taking
precedence over a built-in default.

#### Scenario: Sourcing a config file

- **WHEN** the runner starts and a `ralph.conf` is present beside it (or at the
  path named by `RALPH_CONF`)
- **THEN** it sources that file for `RALPH_*` values before applying defaults
- **AND** an `RALPH_*` value already set in the environment overrides the
  config-file value of the same name

#### Scenario: Working directory is not hardcoded

- **WHEN** the runner is invoked
- **THEN** it changes into the directory named by `RALPH_WORKSPACE` (default: the
  current working directory), never a hardcoded `/workspace`

### Requirement: Single-turn execution with a timeout

The runner SHALL execute exactly one agent turn per iteration, feeding the
project's `PROMPT.md` to the agent, and MUST wrap each turn in a wall-clock
timeout (`RALPH_TURN_TIMEOUT`, default 1200s). A turn that exceeds the timeout
MUST be killed and treated as a no-progress turn rather than left to hang.

#### Scenario: Turn finishes within the timeout

- **WHEN** a turn completes before `RALPH_TURN_TIMEOUT`
- **THEN** the runner records the turn's exit code and whether it produced a new
  commit, then proceeds to the next iteration

#### Scenario: Turn exceeds the timeout

- **WHEN** a turn runs longer than `RALPH_TURN_TIMEOUT`
- **THEN** the runner kills the turn and counts it as making no commit

#### Scenario: PROMPT.md missing

- **WHEN** the runner starts and no `PROMPT.md` exists in the workspace
- **THEN** it refuses to start and exits non-zero with a diagnostic, rather than
  invoking the agent with no instructions

### Requirement: Commit as the progress signal

The runner SHALL treat a change in `git rev-parse HEAD` across a turn as the sole
objective signal of progress. A turn that does not advance HEAD MUST be counted
as a stall.

#### Scenario: Turn advances HEAD

- **WHEN** HEAD differs before and after a turn
- **THEN** the runner records the turn as committed, capturing the short SHA and
  subject, and resets the consecutive-stall counter to zero

#### Scenario: Turn does not advance HEAD

- **WHEN** HEAD is unchanged across a turn
- **THEN** the runner increments the consecutive-stall counter

### Requirement: Consecutive-stall halt

In loop mode the runner SHALL halt for human review after `RALPH_MAX_STALLS`
(default 2) consecutive no-commit turns, and when it does it MUST write a
non-empty one-line reason to `STATUS.md` and exit non-zero.

#### Scenario: Stall threshold reached

- **WHEN** `RALPH_MAX_STALLS` consecutive turns each make no commit
- **THEN** the runner writes a one-line halt reason to `STATUS.md` and exits
  non-zero

#### Scenario: Progress resets the counter

- **WHEN** a committing turn occurs before the threshold is reached
- **THEN** the stall counter returns to zero and the loop continues

### Requirement: STATUS.md stop signal without false positives

The runner SHALL stop cleanly when a turn writes a stop reason to `STATUS.md`,
but MUST NOT treat a pre-existing breadcrumb as a stop reason. It MUST snapshot
`STATUS.md` at startup and stop only when a turn changes it to new, non-whitespace
content; a blank or whitespace-only `STATUS.md` MUST NOT trip a stop.

#### Scenario: Pre-existing breadcrumb does not halt a fresh loop

- **WHEN** `STATUS.md` is non-empty at loop startup and an ordinary turn runs
  without changing it
- **THEN** the loop continues rather than stopping after one turn

#### Scenario: Turn writes a new stop reason

- **WHEN** a turn changes `STATUS.md` to non-whitespace content different from the
  startup snapshot
- **THEN** the loop prints the reason and exits zero

#### Scenario: Whitespace-only write is ignored

- **WHEN** a turn leaves `STATUS.md` blank or whitespace-only
- **THEN** the loop does not treat it as a stop signal

### Requirement: Usage-limit pause and replay

The runner SHALL NOT count a turn that exits non-zero with a recognizable
usage-limit message as a stall. It MUST instead wait until the limit window
refreshes — computing the wait from the message via the reset helper, falling
back to `RALPH_LIMIT_POLL` (default 900s) on an unparseable message — then replay
the same task by reusing the same turn number.

#### Scenario: Parseable reset time

- **WHEN** a turn prints a usage-limit line with a parseable reset time
- **THEN** the runner sleeps until that window refreshes (plus a small buffer) and
  replays the same task without incrementing the stall counter

#### Scenario: Unparseable reset time

- **WHEN** a usage-limit line cannot be parsed for a reset time
- **THEN** the runner falls back to waiting `RALPH_LIMIT_POLL` seconds, then
  replays the same task

### Requirement: Reset-time helper

The kit SHALL include `until_reset.py`, a pure-stdlib helper that converts a
usage-limit "resets ..." fragment into an integer number of seconds to sleep. It
MUST print the seconds and exit zero on a confident parse, exit non-zero on an
ambiguous fragment so the caller can fall back, and clamp its result to a bounded
range so a misparse can never sleep the loop unreasonably long.

#### Scenario: Confident parse

- **WHEN** the helper is given a fragment containing a clock time (e.g.
  `resets 5am UTC`)
- **THEN** it prints a clamped, buffered seconds value and exits zero

#### Scenario: Ambiguous fragment

- **WHEN** the helper is given a fragment with no recoverable clock time
- **THEN** it exits non-zero and prints nothing usable, signaling the caller to
  fall back to a fixed poll

### Requirement: Gitignored state outputs

The runner SHALL write its runtime state under a single configurable directory
(`RALPH_STATE_DIR`, default `.ralph/`): a `current.json` heartbeat for the turn
running now, a `status.jsonl` append-only git-derived feed of completed turns, a
per-turn log under `log/`, and a `turn` counter. The kit MUST document that this
directory be gitignored.

#### Scenario: Heartbeat and feed are written

- **WHEN** a turn runs to completion
- **THEN** `current.json` reflects the current/idle turn and a record is appended
  to `status.jsonl` with turn number, model, exit code, and commit info

#### Scenario: Counter survives restarts

- **WHEN** the runner is restarted
- **THEN** it resumes the turn counter from the persisted `turn` file rather than
  restarting at zero

### Requirement: One-shot status digest

The kit SHALL include a status-digest command that prints, without requiring the
loop to be running, whether a loop container is up, the current heartbeat, the
last several completed turns, the `STATUS.md` stop state, and recent commits. The
container-name filter it uses MUST be a configured value, not a hardcoded literal.

#### Scenario: Digest with no loop running

- **WHEN** the digest is run while no loop is active
- **THEN** it reports "not running" yet still prints the last recorded turns,
  `STATUS.md` state, and recent commits from the persisted state and git

### Requirement: Single-turn mode

The runner SHALL support a `--once` mode that runs exactly one logged turn and
then exits with that turn's exit code, performing no looping, stall accounting, or
`STATUS.md` stop check.

#### Scenario: Run one turn and exit

- **WHEN** the runner is invoked with `--once`
- **THEN** it runs a single turn, writes its log and state record, and exits with
  that turn's exit code
