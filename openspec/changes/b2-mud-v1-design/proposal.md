## Why

The project has a complete, locked design narrative in `CLAUDE.md`, but no
testable specifications. A Ralph Loop (spec → test → implement → refine) cannot
converge against prose; it needs per-subsystem requirements with concrete
scenarios that translate directly into test cases. This change produces the
full Phase 0 specification corpus so that a fresh Claude Code session can begin
Phase 1 (repository bootstrap) and Phase 2 (implementation) without reopening
any design discussion.

## What Changes

- Add an **architecture overview** (`docs/architecture.md`) fixing the Evennia
  package layout, the contrib usage map, custom module boundaries, the
  persistence model, and the **ascending-AC** convention.
- Add **nine subsystem specs** under `docs/specs/` (one per requirement
  R1–R9), each paired with a terse, testable OpenSpec capability spec and a
  skipped pytest stub suite under `tests/<system>/`.
- Add **five zone outlines** under `docs/specs/zones/` (Keep, Wilderness,
  Caves of Chaos, Shrine of Evil Chaos, Cave of the Unknown).
- Add a **quest catalog** (`docs/specs/quests.md`) of 20–30 quests.
- Resolve every **open question** (season cadence, henchmen economy, faction
  thresholds, economy numbers, leaderboard scope, Cave-of-the-Unknown scope,
  web-client scope) with reasoning in `docs/open-questions.md`; escalate any
  genuinely unauthorized decision to `docs/questions.md`.
- Add a **phased build plan** (`docs/build-plan.md`) ordered smallest-shippable
  first for Ralph Loop iteration, plus a **repository scaffolding plan**
  (`docs/specs/scaffolding.md`).
- **No implementation code.** Test files are stubs marked
  `@pytest.mark.skip(reason="Phase 0 stub — implementation in Phase 2")`.

## Capabilities

### New Capabilities
- `zones`: Modular zone package architecture and the static room/mob/exit/NPC
  data model that every area loads from (R1).
- `faction-system`: Scripted faction-pair states and per-(faction, player)
  standings with threshold-driven transitions (R2).
- `repop`: Tribe-scoped respawn, chief+shaman repop halt, rival scouting
  parties, and the Shrine 24-hour reset (R3).
- `disguised-priest`: Season-rotating spy identity, clue assignment, detection
  paths, exposure flow, and boss transition (R4).
- `henchmen`: Hireable AI followers with OSE loyalty/morale, treasure share,
  per-character cap, and permadeath (R5).
- `seasonal-reset`: Campaign-cycle reset of world state with persistent
  character data and a leaderboard snapshot (R6).
- `death-and-hardcore`: Default XP-loss + corpse-run death, and irrevocable
  opt-in permadeath with a server-wide leaderboard (R7).
- `combat`: OSE-faithful, round-based, ticker-driven combat with ascending AC
  and Vancian spellcasting; includes character creation and OSE class data (R8).
- `quests`: 20–30 quests with givers, prerequisites, steps, rewards, and
  faction/season effects (R9).

### Modified Capabilities
<!-- None. openspec/specs/ is empty; this is a greenfield design. -->

## Impact

- **New files only** — pure documentation plus test scaffolding. No runtime
  code, no `evennia --init` (that is Phase 1), no `tasks.md` generation (the
  build plan is its input, generated in Phase 1).
- **Quality gates**: markdown is outside ruff/mypy; the only executable
  additions are typed, skipped pytest stubs under `tests/<system>/`, already
  covered by `[tool.mypy].files = ["tests"]`.
- **Cross-references** existing ADRs 0001 (Podman), 0002 (Pro/Max auth), 0003
  (uv) and the locked decisions in `CLAUDE.md` §2–§3. Does not reopen them.
- **Downstream**: `docs/build-plan.md` becomes the input to Phase 1's
  `tasks.md`; `docs/specs/` become the canonical specs the Ralph Loop reads
  per the `PROMPT.md` template.
