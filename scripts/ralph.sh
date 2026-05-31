#!/usr/bin/env bash
# Ralph Loop runner for the Keep on the Borderlands MUD.
#
# Designed to run inside the kotb-ralph container, where the project is
# bind-mounted at /workspace. See CLAUDE.md §5 / docs/ralph-loop.md.
#
# Usage:
#   ralph.sh            run turns until STATUS.md is non-empty or SIGINT
#   ralph.sh --once     run exactly ONE logged turn, then exit
#
# Environment:
#   RALPH_MODEL=<id>    if set, passed to claude as --model
#                       (e.g. claude-sonnet-4-6). Unset → account default.
#
# Stop conditions (loop mode):
#   * /workspace/STATUS.md becomes NON-EMPTY (Claude wrote a stop reason).
#     An empty STATUS.md is the normal "loop running" placeholder.
#   * SIGINT (Ctrl-C) from the operator
#
# Every turn — in BOTH modes — is logged to /workspace/.ralph/log/turn-<n>.txt
# so review of a run never requires scrollback.

set -uo pipefail

cd /workspace

once=0
[ "${1:-}" = "--once" ] && once=1

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

mkdir -p .ralph/log
turn_file=.ralph/turn
turn=$(cat "$turn_file" 2>/dev/null || echo 0)

model_args=()
[ -n "${RALPH_MODEL:-}" ] && model_args=(--model "$RALPH_MODEL")

turn_ec=0
run_turn() {
  turn=$((turn + 1))
  echo "$turn" >"$turn_file"
  local log=".ralph/log/turn-${turn}.txt"
  echo "ralph: turn $turn ($(date -Is))${RALPH_MODEL:+ model=$RALPH_MODEL} -> $log"
  claude -p --dangerously-skip-permissions "${model_args[@]}" <PROMPT.md 2>&1 | tee "$log"
  turn_ec=${PIPESTATUS[0]}
  echo "ralph: turn $turn exited $turn_ec ($(date -Is))" | tee -a "$log"
}

trap 'echo; echo "ralph: caught SIGINT at turn $turn, exiting"; exit 130' INT

if [ "$once" -eq 1 ]; then
  echo "ralph: single turn (--once) starting from turn $turn"
  run_turn
  echo "ralph: --once complete — log at .ralph/log/turn-${turn}.txt"
  exit "$turn_ec"
fi

echo "ralph: starting at turn $turn ($(date -Is))"
while true; do
  run_turn
  if [ -s STATUS.md ]; then
    echo "ralph: STATUS.md is non-empty at turn $turn — stopping"
    echo "--- STATUS.md ---"
    cat STATUS.md
    exit 0
  fi
  sleep 30
done
