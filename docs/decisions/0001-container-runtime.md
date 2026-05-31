# 0001 — Container runtime: Podman

Date: 2026-05-30
Status: Accepted

## Context

CLAUDE.md §6 left the runtime open ("Podman or Docker — equivalent for this
use case"). The container's job is to bound `claude --dangerously-skip-
permissions` during the Ralph Loop. Host is Arch Linux, both runtimes
installed, rootless Podman already configured (`subuid`/`subgid` populated
for the user, overlay storage driver active).

## Decision

Use **Podman**, rootless.

## Rationale

- **Rootless by default and verified working on this host.** The whole point
  of containerizing a `--dangerously-skip-permissions` agent is bounded
  blast radius; rootless is strictly better on that axis than a rootful
  Docker daemon, even if both are trusted in practice.
- **No daemon to wedge.** `podman run` is just a process. If the loop
  misbehaves, killing it affects nothing else on the host. Docker's daemon
  model puts unrelated workloads at marginal risk.
- **Systemd-friendly.** `podman generate systemd --user` produces a clean
  unit file if we later want the loop to survive reboots. Docker needs
  extra wrapping.
- **Drop-in Docker CLI compatibility.** The Containerfile uses standard
  Dockerfile syntax; nothing Podman-specific. Switching later is cheap, so
  this is a low-cost decision.
- **CLAUDE.md §6 SELinux note (`:Z` mount flag) is moot on Arch** (no
  SELinux), so mount specs stay simple.

## Consequences

- Build: `make build` (`podman build -t kotb-ralph -f Containerfile .`)
- Run loop: `make loop`
- Run a single turn (debug): `make loop-once`
- Drop into a shell: `make shell`
- If a future host lacks rootless Podman, the Containerfile still builds and
  runs under Docker unchanged — only `make`'s `podman` invocations need
  swapping.

## Considered alternatives

- **Docker.** Equivalent functionality; loses on default-rootless and
  daemon-isolation. No compelling reason to prefer it for a solo build on
  this machine.
- **No container.** Rejected up front in CLAUDE.md §6 — the container
  exists specifically to bound `--dangerously-skip-permissions`.
