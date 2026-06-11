## ADDED Requirements

### Requirement: Status reported from state outputs, no running loop required

The `/ralph-status` skill SHALL report loop status by reading the harness state
outputs in the target workspace — the `current.json` heartbeat, the
`status.jsonl` per-turn feed, `STATUS.md`, and recent `git` history — and MUST
work whether or not a loop is currently running.

#### Scenario: Status with no active loop

- **WHEN** `/ralph-status` runs while no loop is active
- **THEN** it reports "not running" yet still summarizes the last recorded turns,
  the `STATUS.md` stop state, and recent commits from the persisted state and git

#### Scenario: Status during a run

- **WHEN** `/ralph-status` runs while a turn is in flight
- **THEN** it reports the current heartbeat (turn, model, start) alongside the
  recent-turn feed

### Requirement: Replaces the host-side shell digest

The `/ralph-status` skill SHALL fully replace the previous host-side
`ralph-status.sh` digest, so no status shell script is shipped to or run from a
consuming project. It MUST surface the same facts the digest did: whether a loop
container is up, the current/last turns with commit/exit info, the stop signal,
and recent commits.

#### Scenario: No status shell script in the consumer

- **WHEN** a project is set up via `/ralph-init`
- **THEN** status is obtained through `/ralph-status`, and the project carries no
  `ralph-status.sh`

### Requirement: Honest about the stop signal

The skill SHALL report `STATUS.md` as a stop signal only when it holds
non-whitespace content, mirroring the runner's own rule, so it never reports a
blank/whitespace `STATUS.md` as a stop.

#### Scenario: Blank STATUS.md is not a stop

- **WHEN** `STATUS.md` is empty or whitespace-only
- **THEN** `/ralph-status` reports the loop as not stopped on that signal
