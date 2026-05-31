# 0003 — Host Python environment: uv

Date: 2026-05-30
Status: Accepted

## Context

The container handles the Ralph Loop's Python environment in isolation
(see `Containerfile`). But interactive development on the host —
running ruff / mypy / pytest locally, exploring Evennia in a REPL,
running ad-hoc scripts — still needs a managed Python environment.
CLAUDE.md is silent on which tool to use for that.

Three reasonable options:

1. **uv** — Astral's package manager. Fast solver, handles venv
   creation and dependency installation in one tool. Reads our existing
   `pyproject.toml` directly, no config changes required.
2. **`python -m venv` + pip** — the boring, ubiquitous baseline. Zero
   extra tooling; works out of the box.
3. **conda / mamba** — already installed (miniforge) on this host.
   Familiar workflow if conda is in muscle memory.

## Decision

Use **uv** for the host development environment.

## Rationale

- **No conda-specific benefit.** This project has zero binary-heavy
  dependencies (no GIS, no GPU, no NumPy-Pandas-Polars stack). Evennia
  is pure-Python (Django + Twisted). Conda's solver overhead and
  global-env model buy nothing here.
- **Speed matters when iterating.** uv's solver is dramatically faster
  than pip/conda for the install-resolve loop. With a Ralph Loop
  producing commits at a clip, fast `uv sync` after a `git pull`
  keeps the dev cycle tight.
- **Reads `pyproject.toml` directly.** No tool-specific config; if we
  ever switch back to plain pip, nothing breaks. The Containerfile and
  CI both stay on plain `pip install -e .[dev]` and remain unaffected.
- **Where the ecosystem is heading.** uv has become the de facto
  modern default in the Python ecosystem this year. Lower learning
  curve for new contributors than conda; better future-proofing than
  legacy venv+pip.

## Consequences

- Host setup, when interactive development starts (Phase 2+):
  ```
  uv venv
  uv sync --extra dev
  source .venv/bin/activate     # or use `uv run <cmd>` directly
  ```
- `.venv/` is already in `.gitignore` (under the Python section).
- The Containerfile keeps using plain `pip` — no need to install uv
  inside the container, and the container is reproducible without it.
- CI keeps using plain `pip install -e .[dev]` — uv is a host-developer
  convenience, not a deployment requirement.
- If a contributor prefers plain venv or conda, both still work
  unchanged. uv is the recommended default, not a hard requirement.

## Considered alternatives

- **Plain venv + pip.** Works, slower iteration, no real downside
  except speed and the lack of a project-management layer. Acceptable
  fallback if uv is unavailable.
- **conda / mamba.** Works, but slow solver and global env management
  without any of conda's binary-distribution strengths is paying a
  cost for nothing.
- **Poetry / PDM / Hatch.** Heavier project-management frameworks.
  Overkill for a pure-Python project with a simple `pyproject.toml`.
