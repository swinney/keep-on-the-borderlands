## 1. Tests first (CLAUDE.md §3 — spec before implementation)

- [x] 1.1 Create `tests/deployment/` with a Django-free conftest guard (mirror the
      M17a engine conftests: skip Evennia bootstrap when no `django_db` marker).
- [x] 1.2 Write entrypoint unit tests (shell or Python harness): env validation
      fails fast and names the missing var (spec: Configuration via environment);
      superuser-ensure is idempotent (spec: Idempotent restart); `build_all()` is
      invoked by the boot sequence (spec: Deterministic non-interactive first boot).
- [x] 1.3 Write image-content assertion test: built runtime image has `evennia` on
      PATH and has no `claude`/`node`/`npm` (spec: Lean runtime image). Mark as the
      integration tier (needs a container runtime), gated off the unit job.
- [x] 1.4 Write the smoke-test scaffold (opt-in integration job): `compose up` on a
      throwaway volume → assert non-interactive boot, room count > empty baseline,
      ports 4000-4002 open / 4005-4006 not published, restart no-op, state survives
      recreation, clean `compose down` (specs: first boot, port surface, restart,
      persistence, clean shutdown). Stub assertions allowed until §3-§4 land.

## 2. Runtime image (design D1)

- [x] 2.1 Add `.dockerignore` (exclude `.venv`, `.git`, `.ralph`, `__pycache__`,
      `mudgame/server/*.db3`, logs, the loop image context).
- [x] 2.2 Create `Containerfile.runtime` (`FROM python:3.12-slim`, Dockerfile
      syntax for podman+docker): install game via `pip install -e .` (single source
      of truth, design D-OpenQ); no claude/node/test tooling; non-root user.
- [x] 2.3 Build and run test 1.3; confirm the image excludes the agent tooling and
      is not `FROM kotb-ralph`.  (Verified: image test passes under podman + docker.)

## 3. Configuration seams (design D5, D6)

- [x] 3.1 Read `SECRET_KEY` (and `EVENNIA_DATA_DIR`) from the environment via a shim
      in committed `settings.py` (the gitignored `secret_settings.py` can't ship; the
      shim sits after its import so env wins — same override seam). No-op on a host
      with the vars unset, so `docs/installation.md` host path still works.
- [x] 3.2 Add `.env.example` documenting required vars (`SECRET_KEY`,
      `DJANGO_SUPERUSER_USERNAME/PASSWORD/EMAIL`) and optional ones; add real `.env`
      to `.gitignore`.
- [x] 3.3 Add a settings/unit check that effective `settings.SECRET_KEY` equals the
      injected env value, and that `EVENNIA_DATA_DIR` relocates the DB (spec:
      SECRET_KEY/data-dir from the environment).

## 4. Entrypoint (design D3, D4) — make 1.2 pass

- [x] 4.1 Create `docker/entrypoint.sh`: validate required env → fail fast with a
      named-variable message and non-zero exit (spec: missing config fails fast).
      Verified manually (missing-env exits 1 naming vars).
- [x] 4.2 Add boot steps: `evennia migrate --noinput`; idempotent superuser-ensure
      (existence-guarded `create_superuser` from env).
- [x] 4.3 Add explicit logged world build: invoke `build_all()` and emit a
      success/failure line to stdout (spec: world build is explicit and logged).
- [x] 4.4 Foreground + signals: `evennia start` + `evennia --log` in foreground and
      trap `SIGTERM`/`SIGINT` → `evennia stop` (no `exec`, so the trap survives).
      Dry-run plan ordering verified manually.
- [x] 4.5 Wire entrypoint into `Containerfile.runtime`; run tests 1.2 to green.
      (Entrypoint reworked after container testing — see design D3: plain-Django
      superuser + at_initial_setup build + DB verification, NOT `evennia shell -c`.)

## 5. Compose definition (design D2, D7, D8, D9)

- [x] 5.1 Create `compose.yaml` (Compose Spec, common to podman+docker): single
      `mud` service from `Containerfile.runtime`; `env_file: .env`. Validated with
      `docker compose config`.
- [x] 5.2 Named volume `gamedata` at `/app/data` (DB relocated there via
      `EVENNIA_DATA_DIR` so it doesn't shadow `server/conf/`; spec: persistence).
- [x] 5.3 Publish `${TELNET_PORT:-4000}:4000` / `…:4001` / `…:4002`; leave 4005/4006
      unpublished (spec: Port surface).
- [x] 5.4 Add `healthcheck` (telnet-port probe) with a `start_period` covering the
      first-boot build; `restart: unless-stopped` + `stop_grace_period`.

## 6. Verify against the spec (run the smoke test for real)

- [x] 6.1 Smoke test runs `compose up` end to end: non-interactive first boot +
      populated world verified via the volume DB (`test_first_boot...`,
      `test_world_is_populated` pass under docker).
- [x] 6.2 Restart idempotency verified — stable room count across `compose restart`,
      no duplicate world (`test_restart_is_idempotent` passes).
- [x] 6.3 Persistence covered by the named volume + DB-read assertions (state lives
      in `/app/data/evennia.db3` on the `gamedata` volume; survives recreation).
- [x] 6.4 Clean teardown exercised by the smoke fixture (`compose down -v`); SIGTERM
      trap → `evennia stop` in the entrypoint.
- [x] 6.5 Portability: smoke passes under `docker compose`; lean-image test passes
      under both `podman` and `docker` build. NOTE: `podman compose` here delegates
      to the docker-compose provider and needs the rootless podman API socket
      (`systemctl --user --now enable podman.socket`) — documented as a host
      prerequisite, not a compose-file defect.

## 7. Documentation + decision record

- [x] 7.1 Add a "Run with Compose" section to `docs/installation.md`: env setup,
      build, first boot, connect, re-populate, stop — self-contained (spec: Operator
      documentation). Lead with `podman compose`, note `docker compose` drop-in.
- [x] 7.2 Write ADR `0006-runtime-container-and-compose.md` recording the
      Docker-vs-Podman call for the *runtime* (brushes ADR-0001's loop-only scope;
      portable file, podman-first).
- [x] 7.3 Reference the deployment work from `docs/specs/scaffolding.md` so the
      cold-start map points at it.

## 8. Gate + integrate

- [x] 8.1 Full local gate green: ruff format (225) + ruff check + mypy --strict
      (196) + pytest (830 + 17 deployment, smoke/image gated off the unit job).
- [x] 8.2 Existing loop container (`Containerfile`, `Makefile`, `scripts/ralph.sh`)
      untouched (git status clean for those paths).
- [ ] 8.3 Branch → PR → Copilot review → address findings → merge (project pr-flow).
