#!/usr/bin/env bash
# Ralph Loop runner for the Keep on the Borderlands MUD.
#
# Designed to run inside the kotb-ralph container, where the project is
# bind-mounted at /workspace. See CLAUDE.md §5 / docs/ralph-loop.md.
#
# Usage:
#   ralph.sh            run turns until STATUS.md is non-empty, SIGINT, or stall
#   ralph.sh --once     run exactly ONE logged turn, then exit
#
# Environment:
#   RALPH_MODEL=<id>          passed to claude as --model (unset → account default)
#   RALPH_TURN_TIMEOUT=<sec>  per-turn wall-clock cap (default 1200 = 20 min).
#                             A turn exceeding it is killed and counts as a stall.
#   RALPH_MAX_STALLS=<n>      consecutive no-progress turns before the loop halts
#                             for human review (default 2).
#
# Stop conditions (loop mode):
#   * /workspace/STATUS.md becomes NON-EMPTY (Claude wrote a stop reason).
#   * RALPH_MAX_STALLS consecutive turns make no new commit (hung/timed-out or
#     stuck-on-red) — the loop writes STATUS.md and exits 1 rather than spin.
#   * SIGINT (Ctrl-C) from the operator.
#
# Resilience: each turn is wrapped in `timeout`, so a single hung turn is killed
# and automatically RETRIED on the next iteration; the loop only gives up after
# RALPH_MAX_STALLS turns in a row produce no commit.
#
# Status outputs (all under /workspace/.ralph/, gitignored — read via `make status`):
#   log/turn-<n>.txt   per-turn output, line-buffered so `tail -f` is live
#   current.json       heartbeat: the turn running right now (task, model, start)
#   status.jsonl       objective git-derived record appended per completed turn
#   turn               turn counter

set -uo pipefail

cd /workspace

once=0
[ "${1:-}" = "--once" ] && once=1

turn_timeout=${RALPH_TURN_TIMEOUT:-1200}
max_stalls=${RALPH_MAX_STALLS:-2}

if [ ! -f PROMPT.md ]; then
  echo "ralph: PROMPT.md missing in $(pwd) — refusing to start" >&2
  exit 1
fi

# Auth comes from the bind-mounted /home/claude/.claude (populated by
# `make login`). If it isn't there, refuse to start rather than burn turns
# waiting for an interactive login that will never come.
if [ ! -d "$HOME/.claude" ] || [ -z "$(ls -A "$HOME/.claude" 2>/dev/null)" ]; then
  echo "ralph: $HOME/.claude is empty — run 'make login' on the host first" >&2
  exit 1
fi

# Claude Code's config is ~/.claude.json — a SIBLING of ~/.claude (the only
# thing we persist), so it's missing on every fresh container and Claude prints
# a "config not found" notice. Restore it from the newest backup (kept inside
# the persisted .claude/backups) so each container starts clean and quiet.
if [ ! -f "$HOME/.claude.json" ]; then
  newest_backup=$(ls -t "$HOME"/.claude/backups/.claude.json.backup.* 2>/dev/null | head -1)
  if [ -n "$newest_backup" ]; then
    cp "$newest_backup" "$HOME/.claude.json"
  else
    echo '{}' >"$HOME/.claude.json"
  fi
fi

mkdir -p .ralph/log
turn_file=.ralph/turn
turn=$(cat "$turn_file" 2>/dev/null || echo 0)

model_args=()
[ -n "${RALPH_MODEL:-}" ] && model_args=(--model "$RALPH_MODEL")

head_rev() { git rev-parse HEAD 2>/dev/null || echo none; }

# The first unchecked tasks.md task (what the upcoming turn should pick up).
first_task() {
  grep -m1 '^- \[ \] ' tasks.md 2>/dev/null \
    | sed -E 's/^- \[ \] *//; s/⛔ MILESTONE GATE.*/[milestone gate]/'
}

# Emit a status record from RJ_* env vars. mode=current overwrites the
# heartbeat (.ralph/current.json); mode=append adds a line to the objective,
# git-derived feed (.ralph/status.jsonl). No-op if python3 is unavailable.
emit_status() {
  command -v python3 >/dev/null 2>&1 || return 0
  RJ_MODE="$1" python3 - <<'PY' 2>/dev/null || true
import json, os
def opt(k):
    v = os.environ.get(k, "")
    return v if v else None
rec = {
    "turn": int(os.environ.get("RJ_TURN", "0")),
    "task": os.environ.get("RJ_TASK", ""),
    "model": opt("RJ_MODEL") or "default",
    "state": os.environ.get("RJ_STATE", ""),
    "started": opt("RJ_STARTED"),
    "ended": opt("RJ_ENDED"),
    "exit_code": int(os.environ["RJ_EXIT"]) if os.environ.get("RJ_EXIT") else None,
    "committed": os.environ.get("RJ_COMMITTED") == "1",
    "sha": opt("RJ_SHA"),
    "subject": opt("RJ_SUBJECT"),
}
if os.environ["RJ_MODE"] == "current":
    json.dump(rec, open(".ralph/current.json", "w"), indent=2)
else:
    with open(".ralph/status.jsonl", "a") as f:
        f.write(json.dumps(rec) + "\n")
PY
}

turn_ec=0
run_turn() {
  turn=$((turn + 1))
  echo "$turn" >"$turn_file"
  local log=".ralph/log/turn-${turn}.txt"
  local task started ended before after committed sha subject
  task=$(first_task)
  started=$(date -Is)
  before=$(head_rev)

  # Heartbeat: what is running right now (one read, no podman inspection).
  RJ_TURN="$turn" RJ_TASK="$task" RJ_MODEL="${RALPH_MODEL:-}" RJ_STATE="running" \
    RJ_STARTED="$started" emit_status current

  echo "ralph: turn $turn ($started)${RALPH_MODEL:+ model=$RALPH_MODEL} timeout=${turn_timeout}s -> $log"
  echo "ralph:   task -> ${task:-<none>}"
  # stdbuf -oL line-buffers output so `tail -f` shows progress LIVE, not only
  # when the turn ends. timeout sends TERM at the cap, then KILL 30s later.
  stdbuf -oL -eL timeout -k 30 "$turn_timeout" \
    claude -p --dangerously-skip-permissions "${model_args[@]}" <PROMPT.md 2>&1 | tee "$log"
  turn_ec=${PIPESTATUS[0]}
  [ "$turn_ec" -eq 124 ] && echo "ralph: turn $turn TIMED OUT after ${turn_timeout}s" | tee -a "$log"

  after=$(head_rev)
  committed=0
  sha=""
  subject=""
  if [ "$before" != "$after" ]; then
    committed=1
    sha=$(git rev-parse --short HEAD 2>/dev/null || echo "")
    subject=$(git log -1 --format=%s 2>/dev/null || echo "")
  fi
  ended=$(date -Is)

  # Objective, git-derived record of the completed turn.
  RJ_TURN="$turn" RJ_TASK="$task" RJ_MODEL="${RALPH_MODEL:-}" RJ_STATE="done" \
    RJ_STARTED="$started" RJ_ENDED="$ended" RJ_EXIT="$turn_ec" \
    RJ_COMMITTED="$committed" RJ_SHA="$sha" RJ_SUBJECT="$subject" emit_status append
  RJ_TURN="$turn" RJ_TASK="$task" RJ_MODEL="${RALPH_MODEL:-}" RJ_STATE="idle" \
    RJ_STARTED="$started" RJ_ENDED="$ended" RJ_EXIT="$turn_ec" \
    RJ_COMMITTED="$committed" RJ_SHA="$sha" RJ_SUBJECT="$subject" emit_status current

  if [ "$committed" = 1 ]; then
    echo "ralph: turn $turn exited $turn_ec ($ended) — committed $sha: $subject" | tee -a "$log"
  else
    echo "ralph: turn $turn exited $turn_ec ($ended) — no commit" | tee -a "$log"
  fi
}

trap 'echo; echo "ralph: caught SIGINT at turn $turn, exiting"; exit 130' INT

if [ "$once" -eq 1 ]; then
  echo "ralph: single turn (--once) starting from turn $turn"
  run_turn
  echo "ralph: --once complete — log at .ralph/log/turn-${turn}.txt"
  exit "$turn_ec"
fi

echo "ralph: starting at turn $turn ($(date -Is)) — timeout ${turn_timeout}s, max-stalls ${max_stalls}"
stalls=0
while true; do
  before=$(head_rev)
  run_turn
  after=$(head_rev)

  # Stop only on a STATUS.md with real (non-whitespace) content. A blank or
  # whitespace-only file is treated as "still running" — a turn that writes
  # stray whitespace must NOT trip a false stop (this bit us once).
  if grep -q '[^[:space:]]' STATUS.md 2>/dev/null; then
    echo "ralph: STATUS.md has a stop reason at turn $turn — stopping"
    echo "--- STATUS.md ---"
    cat STATUS.md
    exit 0
  fi

  if [ "$before" = "$after" ]; then
    stalls=$((stalls + 1))
    echo "ralph: turn $turn produced NO commit (stall ${stalls}/${max_stalls}, exit ${turn_ec})"
    if [ "$stalls" -ge "$max_stalls" ]; then
      printf 'Loop halted: %d consecutive turns made no commit (last exit %d — hung/timed-out or stuck-on-red). Human review needed.\n' \
        "$stalls" "$turn_ec" >STATUS.md
      echo "ralph: ${stalls} consecutive no-progress turns — wrote STATUS.md, stopping"
      exit 1
    fi
  else
    stalls=0
  fi

  sleep 30
done
