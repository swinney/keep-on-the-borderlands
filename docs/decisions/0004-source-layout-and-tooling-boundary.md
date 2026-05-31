# 0004 — Source layout and the ruff/mypy tooling boundary

Date: 2026-05-31
Status: Accepted

## Context

Phase 0 blanket-excluded `mudgame/` from ruff and scoped mypy to `["tests"]`,
because the directory did not yet exist / was 100% generated boilerplate. M1
introduces the first first-party code (`world/rules/`), forcing a decision: how
do the linters and type checker treat the game directory now that it mixes
Evennia-generated plumbing with code we author?

Two sub-questions:
1. **Where does first-party code live** relative to `mudgame/`?
2. **What does each tool police**, so our code is checked without policing
   Evennia's generated files?

Empirical data (M1): a full ruff run over the generated tree found violations
**only** in `mudgame/server/` (3) and `mudgame/web/` (6) — Evennia plumbing.
`mudgame/typeclasses/`, `mudgame/commands/`, and `mudgame/world/` were clean.

## Decision

**First-party code lives under `mudgame/`.** Evennia puts the game dir on
`sys.path` and imports first-party code by game-relative paths (`world.rules.dice`,
`typeclasses.characters.Character`). Top-level packages at the repo root would
not be importable by the running server without path hacks, so they are
rejected.

**ruff:** lint all of `mudgame/` except the Evennia-generated plumbing
(`mudgame/server`, `mudgame/web`). Our code — `world/`, `typeclasses/`,
`commands/` — is linted, including code we hand-write into the generated
typeclass/command stubs later.

**mypy `--strict`:** applies only to **pure, Evennia-free** modules. Scope
starts at `["tests", "mudgame/world/rules"]` and grows as new pure modules land.
Evennia-coupled modules (typeclasses, managers, commands) are kept **out of
strict scope**: their base classes (`DefaultCharacter`, Django models) are
untyped, so `--strict` would drown real findings in unavoidable noise. The
`evennia.*`/`django.*` `ignore_missing_imports` override (commented in
`pyproject.toml`) is restored at M2, when first-party code first imports Evennia.

## Consequences

- The pure rules core is fully lint- and type-checked; the most test-dense,
  bug-prone math gets the strongest static guarantees.
- Engine code is linted (style stays consistent) but not strict-typed. Its
  correctness is covered by `pytest-django` integration tests instead (M2+).
- Adding a new pure module is a two-line chore: create it under a checked path
  and, if it's a new top-level pure package, add it to `[tool.mypy].files`.
- The dependency direction is enforced by convention + review, not the type
  checker: `world/rules/` must never import `evennia`. If it ever needs to, that
  is a design smell to escalate, not silence.

## Considered alternatives

- **Top-level first-party packages (repo root `world/`).** Rejected: not on the
  Evennia import path without extra configuration; diverges from the framework's
  conventional game-dir layout for no benefit.
- **Keep blanket-excluding `mudgame/`.** Rejected: leaves all first-party code
  unlinted and untyped — defeats the quality gates that make the Ralph Loop
  converge (CLAUDE.md §3).
- **mypy `--strict` over the whole game dir.** Rejected: Evennia/Django untyped
  base classes generate intractable error volume; the signal-to-noise ratio
  makes the gate useless.
