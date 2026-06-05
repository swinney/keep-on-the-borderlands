# 0006 — Game runtime container & Compose

Date: 2026-06-05
Status: Accepted

## Context

ADR-0001 chose rootless Podman to bound the Ralph build *loop* — its scope is the
build agent, and the `kotb-ralph` image bakes in Claude Code, node/npm, and the
dev toolchain. Running the *game* for players is a separate mission with different
needs: a lean serving image, persistent state, and a deterministic, non-interactive
boot. The only documented way to run the game today is the hand-driven host path
in `docs/installation.md` (interactive `evennia start` superuser prompt + a silent
first-boot world build), which is unfit for unattended operation.

The `add-game-compose` change introduces a containerized runtime. Two questions
this ADR settles: (1) which container runtime/orchestrator, given ADR-0001 picked
Podman; (2) whether to reuse the loop image.

## Decision

- Ship a **dedicated serving image** (`Containerfile.runtime`, `FROM
  python:3.12-slim`) containing only Evennia + game code. **Not** built on
  `kotb-ralph`.
- Orchestrate with a **single portable `compose.yaml`** (Compose Spec) running one
  `mud` service (Evennia Portal + Server together — not split). It runs unchanged
  under **`podman compose`** and **`docker compose`**.
- **Document `podman compose` first** (rootless, consistent with ADR-0001),
  `docker compose` as a drop-in.

## Rationale

- **Separate, lean image.** A player-facing box should not carry the build agent
  (`--dangerously-skip-permissions` Claude Code) or test/lint tooling — that is
  bloat and needless attack surface. The serving and loop images have different
  lifecycles and dependency sets; keeping them separate keeps each minimal.
- **One service, not two.** Evennia supervises Portal and Server over an internal
  AMP link; splitting them into separate Compose services fights the framework and
  duplicates the data dir. The AMP link (4006) is an internal contract, not a
  service boundary.
- **Portable Compose honors ADR-0001 without reopening it.** ADR-0001 already
  noted "drop-in Docker CLI compatibility." A Compose Spec file that runs under
  both engines gives operators `docker compose` (a common request) while the
  project's own docs and rationale stay Podman-first and rootless. No daemon is
  mandated.
- **Deterministic boot belongs in an entrypoint.** The real complexity —
  non-interactive superuser creation, an *explicit and logged* `build_all()`
  (instead of the silently-swallowed `at_initial_setup` hook), foreground PID 1,
  and a SIGTERM→`evennia stop` trap — lives in `docker/entrypoint.sh`, which is
  independently unit-testable via a dry-run hook.

## Consequences

- New files: `Containerfile.runtime`, `compose.yaml`, `docker/entrypoint.sh`,
  `.env.example`, `.dockerignore`. `settings.py` gains two env-gated seams
  (`SECRET_KEY`, `EVENNIA_DATA_DIR`), both no-ops on the host.
- The DB is relocated to `EVENNIA_DATA_DIR` (`/app/data`) so the named volume does
  not shadow `server/conf/` code; logs stream to stdout.
- Build/run: `podman compose up -d --build` (or `docker compose …`). See
  `docs/installation.md` "Run with Compose."
- The existing loop container (`Containerfile`, `Makefile`, `scripts/ralph.sh`) is
  untouched.
- Tests: a unit tier (entrypoint control-flow, static artifact assertions,
  settings seams) runs in the normal gate; an image/smoke tier is env-gated
  (`RUN_DEPLOYMENT_SMOKE=1`) because it needs a container runtime — mirroring the
  in-process-vs-wire-level split of ADR-0005.

## Considered alternatives

- **Reuse `kotb-ralph` as the serving base.** Rejected: bloat + agent/attack
  surface on a player box; conflated lifecycles.
- **Two services (portal, server).** Rejected: fights Evennia's supervision model.
- **Docker-only (daemon) Compose.** Rejected as the *documented default*: loses
  ADR-0001's rootless/no-daemon posture. Supported as a drop-in via the portable
  file.
- **Postgres service + reverse proxy now.** Deferred: SQLite-in-volume suffices at
  the locked 20-50 concurrent scale; both are documented seams, not built.
- **Mount a volume at `server/`.** Rejected: shadows `settings.py` (DB and code are
  colocated there). Relocating only the DB via `EVENNIA_DATA_DIR` avoids it.
