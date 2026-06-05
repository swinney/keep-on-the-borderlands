#!/usr/bin/env bash
#
# Containerized-runtime entrypoint for Keep on the Borderlands (game-deployment).
#
# Deterministic, non-interactive boot — see openspec/changes/add-game-compose and
# ADR-0006. Sequence:
#   1. validate required env (fail fast, naming the missing var)
#   2. evennia migrate --noinput
#   3. ensure the superuser exists (idempotent; created from env via plain Django
#      so there is NO interactive onboarding prompt and the write commits). This
#      MUST happen before `evennia start`, because at_initial_setup builds the
#      world for account #1 and silently does nothing if it is absent.
#   4. evennia start -l — first boot runs at_initial_setup -> build_all(), then
#      tails Portal+Server logs in the foreground (PID 1 stays alive)
#   5. verify the world actually populated (at_initial_setup swallows tracebacks,
#      so we check the persisted DB and fail loudly on an empty world)
#   6. on SIGTERM/SIGINT (Compose stop) run `evennia stop` for an orderly exit
#
# NOTE: we deliberately avoid `evennia shell -c` — it runs Evennia's interactive
# superuser onboarding before the snippet (which hangs/!skips without a TTY) and
# does not reliably commit. Plain `python -c` with django.setup() autocommits.
#
# Set ENTRYPOINT_DRY_RUN=1 to validate env and print the boot plan without
# executing anything (used by the deployment unit tests).
set -euo pipefail

GAME_DIR="${GAME_DIR:-/app/mudgame}"
DATA_DIR="${EVENNIA_DATA_DIR:-/app/data}"
DB_PATH="${DATA_DIR}/evennia.db3"

log() { printf '[entrypoint] %s\n' "$*"; }
die() { printf '[entrypoint] ERROR: %s\n' "$*" >&2; exit 1; }

# ── 1. Validate required configuration (before any cd, so dry-run needs nothing)
require_env() {
  local missing=()
  local var
  for var in SECRET_KEY DJANGO_SUPERUSER_USERNAME DJANGO_SUPERUSER_PASSWORD; do
    if [ -z "${!var:-}" ]; then
      missing+=("$var")
    fi
  done
  if [ "${#missing[@]}" -gt 0 ]; then
    die "missing required environment variable(s): ${missing[*]} (see .env.example)"
  fi
}

require_env

# ── Dry run: print the plan and stop (control-flow unit tests hook here).
if [ "${ENTRYPOINT_DRY_RUN:-}" = "1" ]; then
  log "plan: cd ${GAME_DIR}"
  log "plan: evennia migrate --noinput"
  log "plan: ensure superuser ${DJANGO_SUPERUSER_USERNAME} (django create_superuser, idempotent)"
  log "plan: evennia start -l  # first boot runs at_initial_setup -> build_all(); foreground"
  log "plan: verify world built (objects > baseline), else fail; SIGTERM -> evennia stop"
  exit 0
fi

cd "$GAME_DIR" || die "game directory not found: ${GAME_DIR}"

# Count rows in a table on the SQLite DB without booting Evennia (0 if missing).
count_rows() {
  python -c "
import sqlite3, sys
try:
    print(sqlite3.connect('${DB_PATH}').execute('select count(*) from ' + sys.argv[1]).fetchone()[0])
except Exception:
    print(0)
" "$1"
}

# ── 2. Database schema.
log "migrating database..."
evennia migrate --noinput

# ── 3. Idempotent superuser (account #1), non-interactively from env. Plain
# Django (not `evennia shell`): no onboarding prompt, and autocommit persists it.
# Idempotent by the *configured username* (not merely "any account exists"), so a
# fresh boot, a restart, or a DB with other accounts all converge correctly.
log "ensuring superuser '${DJANGO_SUPERUSER_USERNAME}'..."
DJANGO_SETTINGS_MODULE=server.conf.settings python -c "
import os
import django

django.setup()
from django.contrib.auth import get_user_model

Account = get_user_model()
name = os.environ['DJANGO_SUPERUSER_USERNAME']
if Account.objects.filter(username=name).exists():
    print('[entrypoint] superuser already present — skipping creation')
else:
    Account.objects.create_superuser(
        name,
        os.environ.get('DJANGO_SUPERUSER_EMAIL', ''),
        os.environ['DJANGO_SUPERUSER_PASSWORD'],
    )
    print('[entrypoint] superuser created')
"

# ── 4+6. Start in the foreground with an orderly shutdown path. First boot runs
# at_initial_setup -> build_all() inside the server process (account #1 exists).
stop() {
  log "received stop signal -> evennia stop"
  evennia stop || true
  exit 0
}
trap stop TERM INT

log "starting Portal + Server (first boot runs at_initial_setup -> build_all)..."
evennia start -l &
app_pid=$!

# ── 5. Verify the world actually built. at_initial_setup swallows tracebacks, so
# trusting it is not enough; we check the persisted result and fail loudly.
log "verifying world build..."
built=""
for _ in $(seq 1 60); do
  if [ "$(count_rows objects_objectdb)" -gt 5 ]; then
    built=1
    break
  fi
  sleep 2
done
if [ -n "$built" ]; then
  log "world build OK ($(count_rows objects_objectdb) objects)"
else
  die "world did not populate (<=5 objects after start) — at_initial_setup/build_all failed; see logs above"
fi

wait "$app_pid"
