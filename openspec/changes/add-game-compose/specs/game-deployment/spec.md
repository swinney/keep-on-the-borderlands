## ADDED Requirements

### Requirement: Lean runtime image

The system SHALL provide a container image dedicated to *serving* the game that
contains the Evennia runtime and the game code, and SHALL NOT contain the
build-loop agent tooling (Claude Code, node/npm) or test/lint tooling that the
existing `kotb-ralph` loop image carries. The serving image SHALL NOT be built
`FROM` the `kotb-ralph` image.

#### Scenario: Serving image excludes the build agent
- **WHEN** the runtime image is built and inspected
- **THEN** no `claude`, `node`, or `npm` executable is present on `PATH`
- **AND** the `evennia` launcher and the project's `world/` packages are importable

#### Scenario: Serving image is independent of the loop image
- **WHEN** the runtime image build is performed
- **THEN** it does not depend on (is not `FROM`) `kotb-ralph`
- **AND** building the runtime image does not require the loop image to exist

### Requirement: Single-service Evennia process model

The Compose definition SHALL run Evennia's Portal and Server together inside one
service container (they supervise each other over the internal AMP link) and
SHALL NOT model Portal and Server as separate Compose services.

#### Scenario: One service runs both Evennia processes
- **WHEN** the stack is started with Compose
- **THEN** a single `mud` service container is running
- **AND** both the Evennia Portal and Server are up inside it (verifiable via the in-container `evennia status`)

### Requirement: Deterministic non-interactive first boot

On a fresh data volume, the entrypoint SHALL bring the game up without any
interactive prompt, performing, in order: database migration; idempotent creation
of the superuser (account #1) from environment variables using plain Django (not
`evennia shell`, which runs an interactive onboarding prompt and does not reliably
commit); then starting the server, whose first-boot `at_initial_setup()` hook runs
`world.build.orchestrator.build_all()`. The superuser SHALL be created before the
server starts, because `at_initial_setup()` builds the world for account #1 and
does nothing if it is absent. The entrypoint SHALL NOT rely on the success of the
silently-swallowed `at_initial_setup()` hook: it SHALL verify the persisted world
and fail loudly on an empty world.

#### Scenario: Fresh boot needs no TTY
- **WHEN** the stack is started for the first time against an empty data volume with no attached TTY
- **THEN** startup completes without blocking on an interactive superuser prompt
- **AND** the configured superuser account exists
- **AND** the world is populated (the object count is greater than the empty-database baseline)

#### Scenario: World build is verified and logged
- **WHEN** first boot runs the world build
- **THEN** the entrypoint checks the persisted database and logs a world-build success line
- **AND** if the world is empty (the hook silently failed) the entrypoint exits non-zero rather than serving a hollow world

### Requirement: Idempotent restart and reboot

Restarting or recreating the service against an existing data volume SHALL NOT
re-prompt for a superuser, SHALL NOT create a duplicate superuser, and SHALL NOT
duplicate world content. The entrypoint's superuser-ensure and `build_all()`
steps SHALL be safe to run on every boot.

#### Scenario: Restart against existing volume is a no-op for setup
- **WHEN** the service is stopped and started again using the same data volume
- **THEN** no interactive prompt appears
- **AND** the superuser account count is unchanged
- **AND** the room count is unchanged (no duplicated world)

### Requirement: Persistent game state across container recreation

The system SHALL store the durable game-state database on a named volume so that
destroying and recreating the container preserves characters, XP, gear, bank
balances, and the leaderboard. Because Evennia colocates the database with the
`conf/` code under `server/`, the database SHALL be relocated to a dedicated data
directory (via `EVENNIA_DATA_DIR`) that the volume mounts, rather than mounting a
volume over `server/` (which would shadow `settings.py`). Server logs SHALL stream
to the container's stdout (captured by the container runtime), not a volume.

#### Scenario: State survives container recreation
- **WHEN** a character with progression exists, the container is removed, and a new container is created against the same named volume
- **THEN** the character and its XP/gear/bank persist
- **AND** the leaderboard entries persist

#### Scenario: The volume does not shadow code
- **WHEN** the data volume is mounted
- **THEN** it mounts a dedicated data directory holding the database, not the `server/` directory
- **AND** `server/conf/settings.py` remains the image's code, unshadowed

### Requirement: Configuration via environment

The runtime SHALL be configured through environment variables rather than baked
image contents. The Django `SECRET_KEY` SHALL be injected via the existing
`secret_settings.py` override seam from the environment, and the superuser
credentials SHALL be supplied via environment variables. The `SECRET_KEY` SHALL
NOT be baked into the image, and recreating the container with the same
`SECRET_KEY` SHALL preserve existing player sessions' validity.

#### Scenario: SECRET_KEY comes from the environment
- **WHEN** the container starts with a `SECRET_KEY` environment variable set
- **THEN** the effective Django `settings.SECRET_KEY` equals the provided value
- **AND** the value is not present in the built image layers

#### Scenario: Missing required configuration fails fast
- **WHEN** the container starts on a fresh volume without the required superuser or secret-key configuration
- **THEN** the entrypoint exits non-zero with a clear message naming the missing variable
- **AND** does not start a half-configured server

### Requirement: Port surface

The Compose definition SHALL expose the player-facing ports — 4000 (telnet), 4001
(web client/website), and 4002 (web client websocket) — and SHALL NOT expose the
Evennia-internal ports 4005 (internal webserver) and 4006 (AMP).

#### Scenario: Player ports reachable, internal ports not exposed
- **WHEN** the stack is running
- **THEN** ports 4000, 4001, and 4002 are reachable from the host
- **AND** ports 4005 and 4006 are not published to the host

### Requirement: Clean shutdown

The entrypoint SHALL handle `SIGTERM` (the signal Compose sends on stop) by
performing an orderly `evennia stop`, so the database is not left in a corrupt or
locked state and a subsequent start succeeds.

#### Scenario: Stop is orderly
- **WHEN** Compose stops the service (sends `SIGTERM`)
- **THEN** the entrypoint runs `evennia stop` and the container exits cleanly within the stop grace period
- **AND** a subsequent start against the same volume boots successfully

### Requirement: Compose portability across runtimes

A single Compose Spec file SHALL define the stack and SHALL run under both
`podman compose` and `docker compose` without per-runtime edits. Operator
documentation SHALL present the `podman compose` path first (consistent with
ADR-0001's rootless rationale) and document `docker compose` as a drop-in.

#### Scenario: Same file runs on either runtime
- **WHEN** the stack is brought up with `podman compose up` and, separately, with `docker compose up`
- **THEN** both start the `mud` service from the same unedited `compose.yaml`

### Requirement: Operator documentation

`docs/installation.md` SHALL document the Compose path end to end: required
environment configuration, building/pulling the image, first boot, connecting,
re-populating, and stopping — sufficient for an operator to run the game via
Compose without reading the code.

#### Scenario: Documented path is complete and self-contained
- **WHEN** an operator follows only the Compose section of `docs/installation.md`
- **THEN** the steps cover configuration, start, connect, and stop
- **AND** no step requires reading source code to succeed
