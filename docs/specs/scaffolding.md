# Repository Scaffolding Plan (Deliverable #11)

The directory layout, dependencies, dev environment, and CI/test runner for the
project. Distinguishes **what already exists** (committed in the bootstrap phase)
from **what Phase 1 adds**. Cross-references `pyproject.toml`, `Containerfile`,
`Makefile`, `.github/workflows/ci.yml`, `.pre-commit-config.yaml`, and ADRs
`0001`–`0003`. This is a plan; it adds no runtime code.

---

## 1. What already exists (do not recreate)

| Area | File(s) | Notes |
|---|---|---|
| Project metadata | `pyproject.toml` | MIT; `requires-python ≥3.12`; ruff/mypy/pytest config; runtime `dependencies = []` until Phase 1 pins Evennia |
| Lint/format | `pyproject.toml [tool.ruff]` | line 100; E/F/W/I/B/UP/SIM/RUF/C4/PL; `mudgame`, `.ralph` excluded |
| Types | `pyproject.toml [tool.mypy]` | `strict`; **`files = ["tests"]`** — expand in Phase 1 (§5) |
| Tests | `pyproject.toml [tool.pytest]`, `tests/` | `testpaths=["tests"]`, strict markers/config; Phase 0 stubs under `tests/<system>/` |
| CI | `.github/workflows/ci.yml` | `ruff format --check` → `ruff check` → `mypy` → `pytest`; 10-min cap; cancels superseded runs |
| Pre-commit | `.pre-commit-config.yaml` | mirrors CI; mypy hook scoped to `^tests/.*\.py$` |
| Container (build loop) | `Containerfile`, `Makefile` | Podman sandbox (ADR 0001); installs evennia + tooling + Claude Code; `make build/login/loop` |
| Container (game runtime) | `Containerfile.runtime`, `compose.yaml`, `docker/entrypoint.sh`, `.env.example` | Lean serving image + Compose (ADR 0006); deterministic non-interactive boot; `game-deployment` spec; podman/docker. See `docs/installation.md` "Run with Compose" |
| Loop runner | `scripts/ralph.sh` | turn logging, STATUS.md stop condition, auth guard |
| Specs workspace | `openspec/` | `spec-driven` schema; the `b2-mud-v1-design` change |
| ADRs | `docs/decisions/0001..0003` | Podman, Pro/Max auth, uv |
| Specs / design | `docs/architecture.md`, `docs/specs/`, `docs/build-plan.md` | this Phase 0 corpus |

`.gitignore` already covers `.ralph/`, `.venv/`, caches, and Evennia runtime
artifacts (`*.sqlite3`, `*.log`).

---

## 2. Target directory structure (post-Phase 1)

```
keep-on-the-borderlands/
├── CLAUDE.md  PROMPT.md  STATUS.md            # PROMPT/STATUS added in Phase 1
├── tasks.md                                   # generated from docs/build-plan.md (Phase 1)
├── pyproject.toml  Makefile  Containerfile
├── docs/            architecture.md, build-plan.md, open-questions.md,
│                    questions.md, specs/**, decisions/**, phases/**
├── openspec/        config.yaml, changes/**, specs/**
├── scripts/         ralph.sh
├── tests/           <system>/  (faction, combat, repop, henchmen,
│                    seasonal_reset, disguised_priest, death, zones, quests)
└── mudgame/                                   # Evennia game dir (Phase 1: `evennia --init mudgame`)
    ├── server/conf/   settings.py, at_initial_setup.py
    ├── commands/      combat, factions, henchmen, quests, default_cmdsets
    ├── typeclasses/   characters, npcs, rooms, exits, objects, scripts
    └── world/
        ├── rules/     ose_tables, classes, spells, dice   (pure, no Evennia)
        ├── factions/  config.py                            (single tuning file)
        ├── managers/  faction, repop, season, priest       (global Scripts)
        └── zones/     keep, wilderness, caves, shrine, unknown
```

Layout rationale is in `docs/architecture.md` §1–§3. Each `world/zones/<zone>/`
and `world/rules/` module is independently testable.

---

## 3. Dependencies

| Scope | Packages | Where declared |
|---|---|---|
| Runtime | `evennia` (pins Django, Twisted transitively) | `pyproject.toml [project.dependencies]` — **filled in Phase 1** once a version is chosen; container already installs it |
| Dev | `ruff`, `mypy`, `pytest`, `pytest-cov`, `pre-commit` | `pyproject.toml [project.optional-dependencies].dev` (present) |
| Dev (Phase 1+) | `pytest-django` | needed to test Evennia/Django-coupled code; container already has it; add to `dev` extras when first-party code imports Django |

The container pins toolchain leaves (`Containerfile`); the host uses uv against the
same `pyproject.toml`. Keeping runtime deps empty until Phase 1 is deliberate
(`pyproject.toml` comment) — nothing first-party imports Evennia yet.

---

## 4. Dev environments

- **Host (interactive), ADR 0003 — uv:**
  ```
  uv venv && uv sync --extra dev      # or: uv pip install -e '.[dev]'
  uv run ruff check . && uv run mypy && uv run pytest
  ```
  `.venv/` is gitignored. Plain `venv+pip` and conda also work (ADR 0003).
- **Container (Ralph Loop), ADR 0001 — Podman:**
  ```
  make build      # builds kotb-ralph from Containerfile
  make login      # one-time Claude Code auth (persisted to .ralph/claude-home)
  make loop       # runs scripts/ralph.sh against PROMPT.md
  ```
  `--dangerously-skip-permissions` is bounded by the container (ADR 0001, 0002).

---

## 5. CI / test runner

CI (`ci.yml`) runs on push/PR to `main`: install `-e .[dev]`, then
`ruff format --check .` → `ruff check .` → `mypy` → `pytest`. Pre-commit mirrors
it locally. Both are the quality gate the Ralph Loop must keep green.

**mypy scope expansion (Phase 1, important):** mypy is currently `files =
["tests"]`. As first-party packages land under `mudgame/world/rules/` etc., add
them to `[tool.mypy].files` and the pre-commit `files` regex, and restore the
Evennia/Django `ignore_missing_imports` override (the commented block in
`pyproject.toml`). Keep `mudgame/` (Evennia's generated scaffold + Django magic)
out of strict scope; type-police only first-party code.

---

## 6. Phase 1 checklist (what bootstrap must add)

1. `evennia --init mudgame`; wire `settings.py` (ticker, gametime, contrib
   activation per `docs/architecture.md` §2) and `at_initial_setup.py` (build
   world, spin up global Scripts).
2. Pin `evennia` in `[project.dependencies]`; add `pytest-django`; restore the
   mypy Evennia/Django override; expand `[tool.mypy].files`.
3. Add `PROMPT.md` (CLAUDE.md §5 template), an empty `STATUS.md`, and generate
   `tasks.md` from `docs/build-plan.md`.
4. Confirm CI stays green with the Evennia game dir present (excluded from ruff;
   `mudgame/` out of mypy strict scope).
5. Begin the Ralph Loop on the smallest-shippable slice in `docs/build-plan.md`.
