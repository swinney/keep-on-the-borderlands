#!/usr/bin/env bash
# One-shot digest of Ralph Loop status — run `make status` or this directly.
# Reads the loop's status outputs under .ralph/ plus git, so it works whether
# or not the loop is currently running.

set -uo pipefail
cd "$(dirname "$0")/.."

echo "=== Ralph Loop status ==="

# Is a loop container running?
if command -v podman >/dev/null 2>&1 \
  && podman ps --filter name=kotb-ralph --format '{{.Names}} {{.Status}}' 2>/dev/null | grep -q .; then
  podman ps --filter name=kotb-ralph --format '  RUNNING: {{.Names}} ({{.Status}})' 2>/dev/null
else
  echo "  not running (no kotb-ralph container)"
fi

echo
echo "--- current turn (.ralph/current.json) ---"
if [ -f .ralph/current.json ]; then
  sed 's/^/  /' .ralph/current.json
else
  echo "  (no heartbeat yet)"
fi

echo
echo "--- recent turns (.ralph/status.jsonl) ---"
if [ -f .ralph/status.jsonl ] && command -v python3 >/dev/null 2>&1; then
  python3 - <<'PY'
import json
try:
    lines = open(".ralph/status.jsonl").read().splitlines()
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
