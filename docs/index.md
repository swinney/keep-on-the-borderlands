# Keep on the Borderlands

An **open-source persistent multiplayer text MUD** adapting the classic 1979
module *B2: The Keep on the Borderlands* to [Evennia](https://www.evennia.com/),
using Old School Essentials (B/X) rules — and built almost entirely by
**Claude Code running as a [Ralph Loop](https://ghuntley.com/ralph/)**.

This site is the project's living documentation.

## Start here

- **[Installation & run guide](installation.md)** — install the game, build and
  populate the world on first boot, and connect by telnet or the web client.
  *(If you want to actually run the MUD, read this.)*
- **[The Ralph Loop — A Field Log](ralph-loop-experiment.md)** — the candid
  story of building this with an unattended agent loop: what worked, what broke,
  and the patterns worth stealing. *(If you're here for the experiment, read
  this.)*
- **[The Ralph-Loop Framework](framework/README.md)** — the portable, project-
  agnostic playbook distilled from this build: the three-layer model (convergence
  machine · dispatch + deployment · operator discipline) you can adopt on a new
  project. *(If you want the reusable method, read this; start with the
  [quickstart](framework/quickstart.md).)*
- **[Architecture overview](architecture.md)** — Evennia structure, the pure
  rules core, the global-Script managers, persistence.
- **[Build plan](build-plan.md)** — the milestone-mapped build order (M0–M14).

## How it's built

Every subsystem follows a strict **spec → test → implement** cycle: a written
spec, a test suite derived from it, then an implementation that passes the
gates (`ruff`, `mypy --strict`, `pytest`). The loop converges against the specs;
hard quality gates and milestone review checkpoints keep it honest.

See the [decision records](decisions/0001-container-runtime.md) for the locked
choices and the [specifications](specs/combat.md) for per-subsystem detail.
