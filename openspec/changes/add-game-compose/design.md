## Context

The game runs today only via the hand-driven `docs/installation.md` path: a host
venv, `evennia migrate`, an **interactive** `evennia start` superuser prompt, and
a first-boot world build wired through Evennia's `at_initial_setup()` hook (whose
tracebacks Evennia silently swallows). This is fine for a developer at a keyboard
and unfit for unattended operation.

The project already containerizes — but for a *different* mission. ADR-0001 chose
**rootless Podman** to bound the `--dangerously-skip-permissions` build agent; the
`kotb-ralph` image bakes in Claude Code, node/npm, and the full dev toolchain. That
image serves the loop, not players, and is the wrong base for a player-facing box.

Relevant existing seams this design reuses without changing their behavior:
- `world.build.orchestrator.build_all()` — idempotent end to end (updates in
  place, skips spawn points already holding a live mob).
- `mudgame/server/conf/secret_settings.py` — the last-imported settings override,
  already gitignored; the natural place to read `SECRET_KEY` from the environment.
- Evennia's launcher: `evennia migrate`, `evennia start -l`, `evennia stop`,
  `evennia status`; Django's `manage.py createsuperuser --noinput`.

Locked constraints that bear on this design: scale is 20-50 concurrent (B2
content); SQLite is the default store; CLAUDE.md §3 requires spec-test-implement;
ADR-0001 favors rootless Podman and notes Docker CLI drop-in compatibility.

## Goals / Non-Goals

**Goals:**
- One declarative `compose.yaml` brings up a fully populated, persistent game.
- First boot is deterministic and needs no TTY (no interactive superuser prompt).
- State (db + logs) survives container recreation on a named volume.
- A lean serving image, independent of the loop image.
- Runs under both `podman compose` and `docker compose` from one file.
- Honor CLAUDE.md §3: ship the `game-deployment` spec (done) + a verifiable test
  approach before writing compose/entrypoint files.

**Non-Goals:**
- Postgres service (SQLite-in-volume suffices at locked scale; leave a seam).
- TLS / reverse proxy / production internet hardening (leave a documented seam).
- Multi-host orchestration, Kubernetes, autoscaling.
- Changing any game-subsystem behavior or its specs.
- Replacing or modifying the existing Ralph-loop container or `scripts/ralph.sh`.

## Decisions

### D1: Serving image is a new lean image, not `kotb-ralph`
A dedicated runtime image `FROM python:3.12-slim` installs only the pinned runtime
deps (`evennia==6.0.0`, `scipy`) plus the game code via `pip install -e .` — no
claude/node/test tooling. *Alternative considered:* reuse `kotb-ralph` — rejected:
bloat and a needless agent/attack surface on a player box. *Alternative:*
multi-stage with a `runtime` target in one Containerfile — acceptable, but a
separate file keeps the loop image's concerns isolated; favor a separate
`Containerfile.runtime` (Dockerfile-syntax, so it builds under both runtimes).

### D2: One `mud` service; Portal+Server stay together
Evennia supervises Portal and Server itself over AMP (4006). The container runs
both via `evennia start -l`. *Alternative considered:* two services (portal,
server) — rejected: fights the framework, duplicates the data dir, and the AMP
link is an internal contract, not a service boundary.

### D3: An entrypoint script owns the deterministic boot
The real design content lives in the entrypoint, not the compose file:
```
1. validate required env (SECRET_KEY, superuser vars) → fail fast if missing
2. evennia migrate --noinput
3. ensure superuser (idempotent): plain `python -c` django create_superuser
   from env, only if no account exists — BEFORE start
4. evennia start -l &            # at_initial_setup -> build_all(); foreground
5. verify world built (poll the DB for objects > baseline) → die if empty
6. trap SIGTERM → evennia stop ; wait on the start process
```
**Hard-won correction (from container testing):** the obvious "call `build_all()`
explicitly via `evennia shell -c`" does NOT work — `evennia shell` runs Evennia's
interactive superuser *onboarding* prompt before the snippet (hangs/skips with no
TTY) and does not reliably commit, so the superuser and world silently vanished
and the container restart-looped. Two fixes: (a) create the superuser with plain
`python -c` + `django.setup()` (Django autocommit, no prompt); (b) let the wired
`at_initial_setup()` build the world during `evennia start` (the path proven on a
real host) — but, because it needs account #1, create the superuser *first*, and
because it swallows tracebacks, *verify* the persisted world (step 5) and fail
loudly instead of trusting it. *Alternative considered:* `evennia shell -c
build_all()` — rejected (prompt + no-commit, above). *Alternative:* trust
`at_initial_setup` silently — rejected (a swallowed failure ships a hollow world);
the step-5 verification is what makes reliance on the hook safe.

### D4: PID 1 / foreground + signal handling
`evennia start` daemonizes and returns, which would make the container exit. The
entrypoint must keep PID 1 alive on the foreground log stream and translate the
container stop signal to `evennia stop`. Approach: `evennia start -l` then `wait`
on it under a `trap`, or a tiny init (`tini`/`--init`) plus an explicit stop trap.
*Alternative considered:* `evennia istart` (foreground) — rejected: it runs only
the Server, not the Portal, so players couldn't connect.

### D5: Superuser created non-interactively from env
Django's `createsuperuser --noinput` reads `DJANGO_SUPERUSER_USERNAME`,
`DJANGO_SUPERUSER_PASSWORD`, `DJANGO_SUPERUSER_EMAIL`. The entrypoint guards it
with an existence check so reboots don't error on "already exists." *Alternative
considered:* a custom Evennia batch script — rejected: reinvents a built-in.

### D6: SECRET_KEY via env through `secret_settings.py`
`secret_settings.py` reads `os.environ["SECRET_KEY"]` (the file is gitignored;
the image ships without it or with an env-reading shim). Keeps the key out of
image layers and stable across recreation, preserving sessions. *Alternative
considered:* Compose `secrets:`/file mount — heavier; revisit if more secrets
appear (e.g., a future DB password).

### D7: Volume scope = a dedicated data dir holding the DB; logs to stdout
Evennia colocates the SQLite DB *and* `conf/` (code) under `server/`, so a volume
mounted at `server/` would shadow `settings.py`. Instead, relocate only the DB to
`$EVENNIA_DATA_DIR` (a one-line settings override, env-gated, no-op on host) and
mount the named volume there. Server logs stream to the container's stdout (the
entrypoint runs `evennia --log`; the runtime captures it) rather than to a volume
— idiomatic for containers and avoids persisting churny log files. *Alternatives
considered:* mount at `server/` — rejected (shadows code); a second volume at
`server/logs/` — rejected (stdout is the container-native log sink). *Future:* a
Postgres service replaces this with the DB container's own volume.

### D8: Port mapping
Publish `4000:4000`, `4001:4001`, `4002:4002`. Do **not** publish 4005/4006. A
future reverse-proxy would front 4001/4002 and publish 443 only.

### D9: Portable Compose Spec, podman-documented
One `compose.yaml` using only Compose Spec features common to both engines. Docs
lead with `podman compose` (ADR-0001 consistency, rootless), `docker compose` as
drop-in. Recorded in a **new ADR** (Docker-vs-Podman for the *runtime*), since it
brushes ADR-0001's loop-only scope. A `healthcheck` uses `evennia status`;
`restart: unless-stopped`.

### D10: Testing approach (CLAUDE.md §3)
The deployment spec's scenarios are verifiable without a player. Favor a
lightweight test harness over a full live server in CI:
- **Image-content assertions** (no `claude`/`node` on PATH; `evennia` present) and
  **entrypoint unit tests** (env validation fails fast; superuser-ensure is
  idempotent; build step is invoked) run cheaply.
- **A smoke test** — `compose up` on a throwaway volume, assert non-interactive
  boot, room count > baseline, ports 4000-4002 open, restart is a no-op, state
  survives recreation, `compose down` is clean — runs as an opt-in/integration
  job (needs a container runtime in CI), not the unit gate. This mirrors M16's
  in-process-vs-wire-level split (ADR-0005).

## Risks / Trade-offs

- **SQLite under a container restart / SIGKILL** → mitigate with D4 orderly stop +
  a stop grace period; WAL mode tolerates the rest. Postgres remains the escape
  hatch if write contention ever shows at the upper scale.
- **`podman compose` vs `docker compose` feature drift** → mitigate by D9
  (restrict to common Compose Spec features; smoke-test on the host's runtime).
- **First-boot `build_all()` slowness blocking the healthcheck** → mitigate with a
  `start_period` on the healthcheck so the build finishes before liveness counts.
- **Secret handling via env is visible to `inspect`/`ps`** → acceptable for a
  self-hosted single operator; D6 note flags Compose `secrets:` as the upgrade.
- **Swallowed first-boot errors** → D3 step 4 makes the build explicit and logged,
  converting a silent empty-world into a visible failure.
- **Scope creep toward "deploy anywhere"** → Non-Goals fence this to local/single
  host self-host; proxy/Postgres are documented seams only.

## Migration Plan

Additive — nothing to migrate. Rollout: build the runtime image → `compose up`
against a fresh named volume (first boot builds the world) → connect on
4000/4001/4002. Rollback: `compose down` (volume retained) or destroy the volume
for a clean slate; the hand-run `docs/installation.md` host path remains valid and
untouched. The Ralph-loop container is unaffected throughout.

## Open Questions

- Image distribution: build-locally-only for v1, or also publish to a registry
  (GHCR)? (Default: build-locally; registry is a later, trivial add.)
- Healthcheck depth: is `evennia status` (processes up) enough, or probe a port /
  a populated-world check? (Default: `evennia status` + `start_period`.)
- Pin the runtime image deps via `pip install -e .` (uses `pyproject`) vs an
  explicit pinned list mirroring the loop image? (Default: `pip install -e .` —
  single source of truth.)
