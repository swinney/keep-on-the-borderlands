#!/usr/bin/env bash
# Ralph Loop runner for the Keep on the Borderlands MUD.
#
# Designed to run inside the kotb-ralph container, where the project is
# bind-mounted at /workspace and ANTHROPIC_API_KEY is in the environment.
# See CLAUDE.md §5 for the surrounding strategy.
#
# Stop conditions:
#   * /workspace/STATUS.md becomes NON-EMPTY (Claude wrote a stop reason).
#     An empty STATUS.md is the normal "loop running" placeholder and does
#     not stop the loop — only a written reason does.
#   * SIGINT (Ctrl-C) from the operator
#
# Each iteration is logged to /workspace/.ralph/log/turn-<n>.txt so review of
# a long unattended run doesn't require scrollback.

set -uo pipefail

cd /workspace

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

trap 'echo; echo "ralph: caught SIGINT at turn $turn, exiting"; exit 130' INT

echo "ralph: starting at turn $turn ($(date -Is))"

while true; do
  turn=$((turn + 1))
  echo "$turn" > "$turn_file"
  log=".ralph/log/turn-${turn}.txt"

  echo "ralph: turn $turn ($(date -Is)) -> $log"
  claude -p --dangerously-skip-permissions < PROMPT.md 2>&1 | tee "$log"
  ec=${PIPESTATUS[0]}
  echo "ralph: turn $turn exited $ec" | tee -a "$log"

  if [ -s STATUS.md ]; then
    echo "ralph: STATUS.md is non-empty at turn $turn — stopping"
    echo "--- STATUS.md ---"
    cat STATUS.md
    exit 0
  fi

  sleep 30
done
