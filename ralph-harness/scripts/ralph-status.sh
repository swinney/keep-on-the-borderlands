#!/usr/bin/env bash
# One-shot digest of Ralph Loop status — project-agnostic. Reads the loop's
# state outputs under $RALPH_STATE_DIR plus git, so it works whether or not the
# loop is currently running.
#
# Config (environment > ralph.conf > default), same loader as ralph.sh:
#   RALPH_WORKSPACE   project dir to inspect       (default: $PWD)
#   RALPH_STATE_DIR   runtime state dir            (default: .ralph)
#   RALPH_CONTAINER   loop container name to probe (default: ralph-loop)
#   RALPH_RUNTIME     container CLI                (default: podman)

set -uo pipefail

# --- config loading: environment > ralph.conf > built-in default ------------
declare -A _env_override
while IFS= read -r _v; do
  [ -n "$_v" ] && _env_override["$_v"]="${!_v}"
done < <(compgen -v | grep '^RALPH_' || true)

conf="${RALPH_CONF:-ralph.conf}"
# shellcheck disable=SC1090
[ -f "$conf" ] && . "$conf"

for _v in "${!_env_override[@]}"; do
  printf -v "$_v" '%s' "${_env_override[$_v]}"
done

cd "${RALPH_WORKSPACE:-$PWD}"

state_dir=${RALPH_STATE_DIR:-.ralph}
container=${RALPH_CONTAINER:-ralph-loop}
runtime=${RALPH_RUNTIME:-podman}

echo "=== Ralph Loop status ==="

# Is a loop container running?
if command -v "$runtime" >/dev/null 2>&1 \
  && "$runtime" ps --filter "name=$container" --format '{{.Names}} {{.Status}}' 2>/dev/null | grep -q .; then
  "$runtime" ps --filter "name=$container" --format '  RUNNING: {{.Names}} ({{.Status}})' 2>/dev/null
else
  echo "  not running (no $container container)"
fi

echo
echo "--- current turn ($state_dir/current.json) ---"
if [ -f "$state_dir/current.json" ]; then
  sed 's/^/  /' "$state_dir/current.json"
else
  echo "  (no heartbeat yet)"
fi

echo
echo "--- recent turns ($state_dir/status.jsonl) ---"
if [ -f "$state_dir/status.jsonl" ] && command -v python3 >/dev/null 2>&1; then
  RJ_FEED="$state_dir/status.jsonl" python3 - <<'PY'
import json, os
try:
    lines = open(os.environ["RJ_FEED"]).read().splitlines()
except OSError:
    lines = []
if not lines:
    print("  (no records yet)")
for line in lines[-10:]:
    try:
        r = json.loads(line)
    except ValueError:
        continue
    mark = "OK " if r.get("committed") else "-- "
    sha = r.get("sha") or "------"
    task = (r.get("task") or "")[:58]
    print(f"  {mark} turn {r.get('turn'):>3} [{r.get('model','?')}] exit {r.get('exit_code')}  {sha}  {task}")
PY
else
  echo "  (no records yet)"
fi

echo
echo "--- STATUS.md (stop signal) ---"
if grep -q '[^[:space:]]' STATUS.md 2>/dev/null; then
  echo "  STOPPED — reason:"
  sed 's/^/    /' STATUS.md
else
  echo "  empty (loop may continue)"
fi

echo
echo "--- recent commits ---"
git log --oneline -6 2>/dev/null | sed 's/^/  /'
