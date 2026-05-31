# Tasks — Keep on the Borderlands MUD

The Ralph Loop's work list, generated from `docs/build-plan.md` (the locked,
milestone-mapped build order). Each unchecked `[ ]` item is intended to be **one
Claude Code session**: a spec→test→implementation slice per `PROMPT.md`.

## How the loop uses this file
- Pick the **first unchecked task**, top to bottom. Order matters — earlier
  milestones are dependencies of later ones.
- Phase 0 already wrote, for every subsystem, a spec (`docs/specs/`) and
  **skipped** test stubs (`tests/<system>/`). So most tasks are "unskip the
  relevant stubs → implement until green," not write-from-scratch.
- A task is `[x]` only when its full spec→test→implementation cycle is done and
  `ruff` + `mypy` + `pytest` are all green (`PROMPT.md` workflow step 7).
- Never weaken a spec or another system's tests to pass (CLAUDE.md §3).
- One subsystem per commit; reference the task/milestone in the message.

Milestone exit criteria and rationale live in `docs/build-plan.md`. Specs live
in `docs/specs/`. Architecture in `docs/architecture.md`.

---

## M0 — Bootstrap (Phase 1, human-run, pre-loop)

- [x] `evennia --init mudgame`; validate boot via `evennia migrate`
- [x] Pin `evennia` in `pyproject` `[project.dependencies]`; add `pytest-django` to dev extras
- [x] Document the per-milestone settings-wiring plan in `mudgame/server/conf/settings.py`
- [x] Harden `scripts/ralph.sh` stop condition to non-empty STATUS.md (`-s`)
- [x] Add `PROMPT.md`; empty `STATUS.md`; generate this `tasks.md` from the build plan
- [x] Confirm CI green with the game dir present (`mudgame/` ruff-excluded, out of mypy strict scope)

### M0 handoff notes for the loop (read before M1)
- **mypy scope:** `[tool.mypy].files` is still `["tests"]` and the Evennia/Django
  `ignore_missing_imports` override is still commented out — deliberately. Expand
  `files` to a first-party package the first time one is created (M1), and
  restore the override the first time first-party code imports `evennia`/`django`
  (M2). Doing either earlier breaks CI (missing path / unused-override warning).
- **ruff vs first-party code under `mudgame/`:** `mudgame/` is ruff-excluded as
  vendored Evennia output, but `world/rules/` etc. are *ours* and must be linted
  and type-checked. M1's first task resolves this: either narrow the ruff exclude
  to only Evennia-generated files, or place first-party packages so they are
  ruff-included. Decide and document in `docs/decisions/`.

---

## M1 — Rules core (pure, no Evennia)

- [x] Resolve the ruff-exclude / mypy-include boundary for first-party `world/rules/`; document in `docs/decisions/`; expand `[tool.mypy].files`
- [x] `dice`: parse/roll `NdM(+K)` with a seeded-RNG seam; `tests/combat/test_dice.py`
- [x] Ability scores + modifiers (OSE table); HP roll by class/HD (`abilities.py`, `progression.py`)
- [x] Ascending-AC attack math: to-hit, nat-20/nat-1 edges, damage application
- [x] Saving throws (OSE save categories by class/level)
- [x] XP thresholds + level lookup per class; morale (2d6 vs morale score)
- [x] All rules-level `tests/combat` scenarios green without booting Evennia (M1 exit)

## M2 — Combat on the engine

- [x] Restore the mypy `evennia.*`/`django.*` override; wire `pytest-django` (`DJANGO_SETTINGS_MODULE`) for engine tests
- [x] `Character`/`Mob` typeclasses; wire AC/HP/abilities onto traits
- [x] Ticker-driven round loop + individual initiative
- [x] `attack` command + a target-dummy mob
- [x] Minimal Vancian spells: light, magic missile, cure light wounds, detect evil; `cast` + memorization-on-rest
- [x] 0 HP triggers a death handoff stub; `tests/combat` engine scenarios green (M2 exit)

## M3 — Death & hardcore

- [x] Corpse object creation at death location with full gear
- [x] Default death: XP loss to start of current level; recall-revive at Inner Bailey
- [x] Hardcore: opt-in flag at creation (irrevocable), deletion on death, leaderboard `fell` entry
- [x] Who-list / title marker for hardcore characters; `tests/death` green (M3 exit)

- [x] ⛔ MILESTONE GATE (M3 → M4 review) — **passed**: M3 reviewed and merged via PR #3.

## M4 — Faction state machine

- [x] `world/factions/config.py`: tribes, initial pair-states, thresholds (single tuning file)
- [x] `faction_manager` global Script: per-player standing + per-pair tension bands
- [x] Event deltas (e.g. kill-count shifts) + decay over time
- [x] NPC aggression binding from standing; `consider` command
- [ ] `tests/faction` green, incl. shared-enemy thaw arithmetic (M4 exit)

- [ ] ⛔ MILESTONE GATE (M4 → M5 review). When every M4 box above is checked,
  do NOT begin M5. As your entire action this turn, write the single line
  `M4 complete — paused for human review before M5.`
  to `STATUS.md` and stop. Make no code changes and do not check this box.

## M5 — Henchmen

- [ ] Tavern roster + hire flow (reaction roll, hire cost, CHA-table cap)
- [ ] Follow + basic order commands; combat AI
- [ ] Loyalty/morale: flee or refuse below threshold (OSE)
- [ ] XP + treasure share; permadeath + re-hire; `tests/henchmen` green (M5 exit)

## M6 — Repop + seasonal reset

- [ ] Spawn-point registration + 15-min respawn
- [ ] Leadership halt: chief AND shaman dead → 60-min repop freeze
- [ ] Rival-tribe scouting into the dead window + faction-pair shift
- [ ] Shrine 24h reset cycle + server broadcast
- [ ] `season_manager`: orchestrate per-manager reset hooks; leaderboard snapshot; `end_season`
- [ ] Persistence check: characters/XP/gear/bank survive reset; `tests/repop` + `tests/seasonal_reset` green (M6 exit)

## M7 — Keep zone

- [ ] Build `world/zones/keep/` rooms + exits (recall = Inner Bailey)
- [ ] Provisioner shop + economy (starting gold, pricing, gold sinks); bank
- [ ] Tavern henchman roster integration; chapel staff NPCs (priest pool placeholder)
- [ ] Rest / spell memorization in the Keep; new character spawns→equips→hires→rests (M7 exit)

## M8 — Wilderness zone

- [ ] `world/zones/wilderness/` hex map on `xyzgrid`; travel commands
- [ ] Wandering-encounter tables
- [ ] Set-pieces: hermit, spider lair, mountain lions, raiders
- [ ] Travel Keep → ravine mouth works end-to-end (M8 exit)

## M9 — Kobold cave vertical slice ⭐ (critical integration milestone)

- [ ] `world/zones/caves/` kobold lair rooms + kobold mobs
- [ ] Kobold chief + shaman leaders wired to the M6 leadership-halt + rival scouting
- [ ] Faction standing shifts observable in kobold behavior (ties M4 ↔ M9)
- [ ] Guildmaster tribe-clearing quest + treasure→XP-on-secure loop
- [ ] Integration test: spawn → equip → hire → travel → clear tribe → return → turn in → bank for XP (M9 exit)

## M10 — Remaining caves

- [ ] Orc Vile Rune + Orc Decapitator (the playable war rivalry)
- [ ] Goblins + ogre ally
- [ ] Hobgoblins (King Nardo)
- [ ] Bugbears
- [ ] Gnolls + owlbear
- [ ] Minotaur maze + Shrine passage; faction rivalries + repop halts fire under test (M10 exit)

## M11 — Shrine

- [ ] `world/zones/shrine/` temple rooms; `no_recall` deep rooms
- [ ] The Adept boss
- [ ] 24h reset wired to the M6 cycle
- [ ] Destructible altar → `end_season`; reset + season-end trigger tested (M11 exit)

## M12 — Disguised priest

- [ ] `priest_manager`: seasonal rotation with no back-to-back identity repeat
- [ ] Clue assignment from the pool
- [ ] Four detection paths: Detect Evil, Curate dialogue, witnessed nighttime act, planted object
- [ ] Spy quest chain (3+ → Caves ambush)
- [ ] Exposure → server-global event → spy flees to Shrine boss
- [ ] `tests/disguised_priest` green, incl. two-season-rotation scenario (M12 exit)

## M13 — Quest catalog

- [ ] Wire all 24 quests across givers (Castellan, Curate, Guildmaster, Provisioner, Hermit, chiefs, priest)
- [ ] Faction gating + repeatable/story state per character
- [ ] Season-global effects (expose priest, destroy Shrine); `tests/quests` green (M13 exit)

## M14 — Polish & scale

- [ ] Economy / XP-pacing balance pass (target ~L10 in a 6-week season)
- [ ] 50-player <100ms command-latency measurement (acceptance criterion)
- [ ] Web-client theming + MOTD
- [ ] Encounter-table tuning; all OpenSpec acceptance criteria demonstrably met (M14 exit)

## Deferred follow-ups

- [ ] **Spell disruption via combat-round timing** (combat.md §5): make `cast`
  *declare* a spell (set `spell_declaring`) and resolve it at end of round via
  the `CombatHandler`, so damage taken before resolution disrupts it. M2 shipped
  the `apply_damage` hook but left it inert (synchronous casting never declares);
  this needs the round loop's declare→resolve phases. Re-enables the skipped
  `tests/combat/test_combat.py::test_damage_disrupts_unresolved_cast`.

---

When every box above is checked, the loop writes "RALPH: project complete" to
`STATUS.md` and exits (`PROMPT.md` stop condition).
