## ADDED Requirements

### Requirement: Machinery baked into the image, not the project

The base image SHALL bake the runner machinery (`ralph.sh`, `until_reset.py`) onto
`PATH` (e.g. `/usr/local/bin`) so a consuming project carries **no** copy of those
scripts. The machinery MUST exist in exactly one source (the `keep-on-ralphing`
repo's base build context); a consuming project that `FROM`s the base image gets
the machinery without vendoring it.

#### Scenario: Consumer carries no machinery

- **WHEN** a project builds its image `FROM` the published base and the container
  runs the loop
- **THEN** `ralph.sh` resolves from the image's `PATH`, and the project repo
  contains no `scripts/ralph.sh` (or equivalent) copy

#### Scenario: Single source of the runner

- **WHEN** the runner logic needs a fix
- **THEN** it is changed once in the base build context and every consumer picks it
  up by rebuilding/pulling the base — no per-project edit

### Requirement: Thin consumer Containerfile with one toolchain seam

The base image SHALL be consumable via a minimal project `Containerfile` that does
no more than `FROM` the base and install the project's own toolchain. The base
MUST already provide the generic layer (OS tools, Node, the Claude Code install,
a UID/GID-matched non-root user) so the consumer edits only its toolchain.

#### Scenario: Minimal consumer image

- **WHEN** a project needs its sandbox
- **THEN** a `Containerfile` of `FROM <base>` plus a single toolchain-install block
  builds a working loop sandbox, with no other base-layer edits required

### Requirement: Local, registry-free build

The base image SHALL build locally from the repo with a single command
(`make build-base`) and require no container registry. The build MUST match the
host UID/GID (overridable build args) so files written under the workspace bind
mount are host-owned. Pushing to a registry (GHCR) MAY be added later but MUST NOT
be required to use the harness.

#### Scenario: Build with no registry

- **WHEN** a teammate clones `keep-on-ralphing` and runs `make build-base` on a
  Linux/podman host
- **THEN** a usable base image is produced locally with no registry login or pull

### Requirement: Linux + podman, single architecture

The base image SHALL target Linux hosts with podman and a single architecture. It
MUST NOT claim or require multi-arch, macOS, Windows, or Docker support; any
runtime assumptions (podman, the host arch) are stated in the repo's README.

#### Scenario: Scope is stated, not overclaimed

- **WHEN** a reader consults the base image's documentation
- **THEN** it states Linux + podman + single-arch as the supported target and does
  not imply tested Docker/macOS/Windows/multi-arch support
