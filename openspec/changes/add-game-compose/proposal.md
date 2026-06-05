## Why

The game can only be run today by hand-following `docs/installation.md` on a host
with Python 3.12, a venv, an interactive `evennia start` superuser prompt, and a
silent first-boot world build. That path is fragile to reproduce and impossible
to operate unattended. A containerized, Compose-orchestrated runtime turns "run
the MUD" into one declarative file with persistent state, a non-interactive first
boot, and a clean stop/restart story — without disturbing the existing Ralph-loop
container, which serves a different purpose (bounding the build agent, not serving
the game).

## What Changes

- **New lean runtime image** for *serving the game* (Evennia + game code only),
  distinct from the existing `kotb-ralph` loop image (which bakes in Claude Code,
  node, and dev tooling and must not be the serving base).
- **A portable `compose.yaml`** (Compose Spec) defining a single `mud` service —
  Evennia's Portal+Server run together in one container (they supervise each other
  over internal AMP; they are **not** split into two services).
- **A non-interactive entrypoint** that makes first boot deterministic:
  `migrate` → ensure-superuser-from-env via plain Django (idempotent by username;
  no onboarding prompt; account #1 must exist before the build) → `evennia start
  -l` in the foreground, whose first-boot `at_initial_setup` hook runs
  `build_all()` → **verify** the persisted world and fail loudly if empty (the hook
  swallows tracebacks) → trap `SIGTERM` to `evennia stop`.
- **Env-injected `SECRET_KEY`** via the `settings.py` env shim (sitting after the
  `secret_settings.py` import so it wins), so the key is stable across container
  recreation and never baked into the
  image.
- **A named volume** for persistent game state (the SQLite database + logs under
  `mudgame/server/`), so characters, XP, gear, bank, and the leaderboard survive
  container recreation.
- **Exposed player ports** 4000 (telnet), 4001 (web), 4002 (websocket); internal
  ports 4005/4006 (webserver/AMP) stay unexposed.
- **Operator documentation** in `docs/installation.md` (a Compose quick-start) and
  a new ADR recording the Docker-vs-Podman call for the *runtime* (it brushes
  ADR-0001, which chose Podman for the loop). Compose runs under both
  `podman compose` (documented first, consistent with ADR-0001's rootless
  rationale) and `docker compose` (drop-in).

Out of scope for this change (documented seams, not built): a Postgres service
(SQLite-in-volume suffices at the locked 20-50 concurrent scale) and a
TLS-terminating reverse proxy (production hardening).

## Capabilities

### New Capabilities
- `game-deployment`: How an operator builds, configures, runs, persists, and stops
  the game as a containerized service via Compose — image contents, the
  deterministic non-interactive boot sequence, state persistence, configuration
  injection, port surface, and lifecycle.

### Modified Capabilities
<!-- None. No existing game-subsystem requirement changes; the entrypoint reuses
     existing seams (build_all idempotency, secret_settings override, the
     inner_bailey recall tag) without altering their specified behavior. -->

## Impact

- **New files:** a runtime `Containerfile`/`Dockerfile` (or a `runtime` stage),
  `compose.yaml`, an entrypoint script, a `.env.example`, and a new ADR under
  `docs/decisions/`.
- **Modified files:** `docs/installation.md` (add Compose path),
  `docs/specs/scaffolding.md` (reference the deployment spec), `.gitignore`
  (ignore a real `.env`), `.dockerignore` (new).
- **Unaffected:** the existing `Containerfile`, `Makefile`, and `scripts/ralph.sh`
  loop tooling; all game-subsystem code and tests.
- **Dependencies:** no new Python deps; relies on Evennia 6.0.0 launcher
  behavior and Django `createsuperuser --noinput`. Requires `podman compose` or
  `docker compose` on the host.
- **Constraint:** per CLAUDE.md §3 (spec-test-implement), the `game-deployment`
  spec and a test approach must exist before the compose/entrypoint files are
  written.
