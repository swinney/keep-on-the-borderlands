# Phase 0 brief — Specification Generation

This file is the canonical brief for the Phase 0 Claude Code session that
drives OpenSpec against `keep-on-borderlands-openspec-prompt.md` to produce
the 11 design deliverables CLAUDE.md depends on.

It's saved here so the brief is reproducible — paste the section below
verbatim as the first message of a fresh `claude` session running in this
repository.

Future phases get their own briefs in this directory
(`docs/phases/phase-1-*.md`, etc.).

---

Drive **Phase 0 — Specification Generation** for the Keep on the Borderlands MUD.

You are running in the project's local folder. The OpenSpec skills, existing ADRs, project configuration, and git remote all live here.

## Repository

`~/Projects/keep-on-the-borderlands` — public at https://github.com/swinney/keep-on-the-borderlands, on `main`, CI green. Existing commits cover project context + container scaffolding + OpenSpec setup, LICENSE + README, quality gates (ruff / mypy --strict / pytest / pre-commit / CI), ADR 0003 (uv for host Python env), and this brief file.

## Required reading before doing anything else

1. **`CLAUDE.md`** — the full design context. Locked decisions in §2, architectural patterns in §3, the OpenSpec prompt in §4, the Ralph Loop strategy in §5. Read it end to end before touching anything else. Sections 2 and 3 are non-negotiable; don't reopen them.
2. **`keep-on-borderlands-openspec-prompt.md`** — the canonical OpenSpec prompt with full requirements (R1–R9), acceptance criteria, and the list of 11 deliverables.
3. **`docs/decisions/0001-container-runtime.md`**, **`0002-claude-auth.md`**, and **`0003-host-python-environment.md`** — already-recorded ADRs (Podman, Pro/Max subscription auth, uv). Don't duplicate; cross-reference if relevant.
4. **`.claude/skills/openspec-propose/SKILL.md`**, **`openspec-explore/SKILL.md`**, **`openspec-apply-change/SKILL.md`**, **`openspec-archive-change/SKILL.md`** — read each before invoking. The OpenSpec workflow lives in these skills; use them rather than approximating spec output by hand.
5. **`openspec/config.yaml`** and the empty `openspec/specs/` + `openspec/changes/` directories — the OpenSpec workspace, already scaffolded.

## Goal

Produce the 11 deliverables listed at the bottom of `keep-on-borderlands-openspec-prompt.md`:

1. Architecture overview → `docs/architecture.md`
2. Per-subsystem specs for R1–R9 → `docs/specs/<system>.md`
3. Test plan and test stubs for each subsystem → `tests/<system>/` (stubs only — no implementation)
4. Faction system design doc → `docs/specs/faction.md` (data model, transition rules, config schema, initial B2 tribe states)
5. Zone outlines for all five zones → `docs/specs/zones/{keep,wilderness,caves,shrine,unknown}.md`
6. Quest catalog → `docs/specs/quests.md`
7. Henchmen design doc → `docs/specs/henchmen.md`
8. Seasonal reset spec → `docs/specs/seasonal-reset.md`
9. Disguised Priest spec → `docs/specs/disguised-priest.md`
10. Phased build plan structured for Ralph Loop iteration → `docs/build-plan.md` (smallest-shippable first)
11. Repository scaffolding plan → `docs/specs/scaffolding.md` (cross-reference existing `pyproject.toml` and `Containerfile`)

## Open questions OpenSpec must propose answers to (with reasoning)

See the "Open questions" section of `keep-on-borderlands-openspec-prompt.md`: season length and cadence, henchmen specifics, faction transition thresholds, economy numbers, leaderboard scope, Cave of the Unknown disposition, web client customization scope. License (MIT) and host Python env (uv) are already decided.

Anything that cannot be answered from CLAUDE.md context goes into `docs/questions.md` rather than being invented.

## Workflow

- Use the OpenSpec propose/apply/archive skills as designed — that's why they're configured in `.claude/skills/`.
- One logical unit per commit (e.g. "architecture overview", "faction system spec", "Keep zone outline"). Don't batch everything into one mega-commit.
- Each commit must pass the local CI gates: `ruff format --check . && ruff check . && mypy && pytest`. The pre-commit hooks (`.pre-commit-config.yaml`) enforce this.
- mypy is currently scoped to `tests/` (see `pyproject.toml [tool.mypy].files`). Test stubs you add under `tests/<system>/` are already covered. Don't add packages outside `tests/` to mypy until Phase 2.
- Markdown files don't go through ruff/mypy — most Phase 0 commits will only need pytest + basic pre-commit hooks to be green.
- If a test stub is added without an implementation, mark it with `@pytest.mark.skip(reason="Phase 0 stub — implementation in Phase 2")` so CI stays green.
- Push to `origin/main` after each successful commit so progress is visible.

## Out of scope

- **No implementation code.** Pure specification phase. If you find yourself writing function bodies that do real work, stop — that's Phase 2.
- **No `evennia --init mudgame` yet.** That's Phase 1 (repository bootstrap). Specs reference Evennia's structure abstractly; they don't require it to exist on disk.
- **No `tasks.md` generation yet.** The phased build plan (deliverable 10) is the input that gets transformed into `tasks.md` in Phase 1.
- **No changes to locked decisions.** §2 of CLAUDE.md and the three existing ADRs are settled. If you discover a real conflict, surface it in `docs/questions.md` rather than reopening.

## Stop conditions

- All 11 deliverables exist as committed files and CI is green → write `Phase 0 complete` to `STATUS.md` and stop.
- A decision is required that CLAUDE.md does not authorize and no sensible default exists → write the question to `docs/questions.md` and stop without committing speculative content.
- Tests have been red for 3 consecutive commits on the same deliverable → stop and write the situation to `STATUS.md` for human review.

## Acceptance

Phase 0 is done when:
- The 11 deliverables are present and internally consistent.
- A reader can hand the repo to a fresh Claude Code instance for Phase 1 (repository bootstrap + Ralph Loop setup) without further design discussion.
- Open questions are either resolved with reasoning or explicitly logged.
- CI is green on `main`; latest commit is pushed to `origin/main`.
