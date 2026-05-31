# Keep on the Borderlands MUD — Project Memory

This file captures the full design context for the project so any future Claude
session (Claude Code on Linux, a fresh Cowork chat, etc.) can pick up cold and
start work without re-deriving decisions. Read this end-to-end before acting.

---

## 1. Project Overview

Build an **open-source persistent multiplayer text MUD** that adapts module
**B2: The Keep on the Borderlands** (Gary Gygax, 1979) as the opening campaign
arc of a larger possible D&D-flavored MUD.

- **Target audience:** Players familiar with classic MUDs and/or old-school D&D.
- **Surface:** Telnet plus Evennia's default web client.
- **Scale target:** 20–50 concurrent players in the B2 content without
  trivializing it.
- **Implementation model:** Built by Claude Code using a Ralph Loop
  (iterative spec → test → implement → refine). Spec quality and testability
  are first-class concerns, not afterthoughts.
- **Host machine:** Development and runtime on a Linux machine (this file
  was authored from a macOS Cowork session over sshfs; project lives on Linux).

---

## 2. Locked Decisions

These were settled through deliberate discussion. **Do not reopen them
without explicit user input.** Each has rationale captured so future-Claude
doesn't second-guess.

### Engine: Evennia (Python)

- Open-source MUD framework, Python 3, Django ORM for persistence.
- **Why:** Modern stack, mature MUD primitives, real web client, large
  ecosystem of contribs to lift instead of building from scratch. The
  Diku/ROM C codebase alternative was rejected because the dev velocity
  cost is enormous and the codebase will be Claude-Code-maintained, where
  Python is dramatically more reliable than C.
- **Use Evennia contribs aggressively** where they fit: `traits`, `rpsystem`,
  `combat`, `clothing`, and any others that reduce custom code surface.
  Override only where OSE rules demand it. Document every contrib used
  (and every contrib rejected in favor of custom code) in
  `/docs/decisions/`.

### License: Open source (specific choice TBD)

OpenSpec to propose between MIT, Apache 2.0, and AGPL with reasoning.
Default lean: MIT for maximum adoption, unless there's a reason to prefer
copyleft.

### Ruleset: Old School Essentials (OSE)

- B/X retroclone (Moldvay Basic / Cook Expert).
- **Why:** B2 was actually written for B/X, not AD&D 1e. OSE has an open
  license whose SRD text can be used directly. B/X has ~⅓ the rule
  surface of AD&D 1e, cleaner spell lists, no weird racial level caps,
  and fewer cross-system interactions to bug-fix in a Ralph Loop.
- Race-as-class (Dwarf, Elf, Halfling) per OSE Core Rules.
- Classes: Cleric, Fighter, Magic-User, Thief, plus the three race-classes.
- No multiclass in v1.

### Level Range for B2 Content: 1–10

MUD-scaled from the module's 1–3. B2 carries players to roughly mid-game;
content past the Shrine is out of scope for v1 but should not be ruled out
architecturally.

### World Persistence: Seasonal Resets

- Each season is a campaign cycle.
- **What persists at reset:** Player characters, XP, gear, bank balance,
  leaderboard.
- **What resets:** Faction states, repop counters, Shrine state, disguised
  Priest identity and clue assignments, season-global quest effects.
- **Why:** Lets the world react meaningfully to player action (the whole
  point of B2) without requiring infinite content. Full persistence creates
  a content treadmill; standard Diku-style 15-min total repop kills the
  political layer.

### Faction System: Scripted States

- Per tribe pair: state ∈ {allied, peaceful, tense, war}.
- Per (faction, player): standing ∈ {friendly, neutral, hostile, kill-on-sight}.
- Transitions are **rule-based with thresholds**, not full simulation.
  Example: killing 5+ kobolds shifts (kobold, player) from neutral to
  hostile to kill-on-sight, and shifts (kobold, goblin) from tense to
  peaceful.
- Initial faction-pair states mirror the module's described politics.
- All thresholds in a single config file for tuning without code changes.
- **Why scripted over emergent:** Reactive enough to feel alive, but
  testable and bug-bounded — important for Ralph Loop iteration.

### Solo Viability: Henchmen

- Hire from a roster at the Keep's tavern (canon to B2 — module explicitly
  suggests hiring men-at-arms).
- AI-controlled NPCs that follow, fight, and demand a share of XP/treasure.
- OSE loyalty/morale rules; flee or refuse orders below thresholds.
- Per-character cap (OpenSpec to propose number).
- Permadeath for henchmen; replacements must be re-hired.
- **Why:** Solves low-population grouping problem, period-appropriate,
  no forced-grouping fragility.

### Death Penalty (Default): XP Loss + Corpse Run

- On death: lose XP back to the start of current level.
- Corpse persists at death location with all gear; retrievable by walking
  back.
- Classic, easy to implement, easy to test.

### Death Penalty (Hardcore Opt-In): Permadeath + Leaderboard

- Opt-in at character creation, **irrevocable**.
- On death: character deleted; final level and season added to a
  server-wide leaderboard.
- Hardcore characters visually flagged (title, who-list marker).
- Leaderboard scope (per-season vs all-time vs both) TBD by OpenSpec.

### Disguised Priest Plot: Rotating Identity

The module's most interesting NPC is an evil priest disguised in the Keep's
chapel. Adapting this to a persistent multiplayer world is the hardest
narrative problem in B2.

- **Mechanism:** At each season start, the spy is randomly assigned to one
  of N chapel NPCs. Clues (`lights candles at midnight`, `owns a black-
  handled dagger`, `knows the Shrine's password`, etc.) are randomly
  assigned from a pool.
- The spy offers quests that subtly aid the Shrine; completing 3+ triggers
  a scripted ambush in the Caves.
- Detection paths: high-level Detect Evil, Curate dialogue branch,
  witnessing a scripted nighttime act, finding a planted object.
- Reporting to the Castellan triggers a server-global "exposed" event;
  the spy flees to the Shrine and becomes a boss there.
- Resets at season boundary.
- **Why rotating:** Sidesteps the "first player wins forever" problem of
  server-global one-shot secrets without breaking the shared-world
  illusion of per-player instancing.

### PvP: Disabled in v1

Adds enormous edge-case complexity for little payoff at this population.
Easy to add later.

### Repop Model: Tribe-Scoped

- Standard mobs: 15-minute respawn.
- Killing a tribe's chief AND shaman halts that tribe's repop for 60 real
  minutes.
- During the dead-tribe window, a designated rival tribe spawns scouting
  parties into the empty caves; rival's faction-pair state with the
  player may shift.
- Shrine of Evil Chaos: 24-hour reset cycle with server-wide broadcast
  ("the cult regroups in the deep places").

### Recall Point: Inner Bailey of the Keep

### No GM Tooling in v1

Build the systems, see what emerges, decide later.

---

## 3. Architectural Patterns (Locked)

### Spec-Test-Implement, Strictly Enforced

This is what makes the Ralph Loop converge. Every subsystem
(faction, repop, quests, combat, henchmen, seasonal reset, disguised
Priest, death penalty, etc.) requires:

1. A written spec in `/docs/specs/<system>.md`.
2. A unit test suite in `/tests/<system>/` derived from the spec.
3. An implementation that passes those tests.

**No implementation work begins on a subsystem before its spec and test
scaffold exist.** This is non-negotiable for Ralph Loop quality.

### Type Safety: `mypy --strict` on All Custom Modules

Type hints everywhere. Catches a huge class of integration bugs the loop
would otherwise introduce.

### Lint: `ruff` with sensible defaults

### Modular Zones

Each zone is its own Python package under `/world/zones/`, not a monolithic
data file. Easier for the loop to work on one zone without breaking another.

### Persistence

Use Evennia's Django ORM for player and world state. Flat files only for
static area definitions where they make sense.

### Repository Conventions

- One subsystem per commit; commit messages reference the task ID.
- Never modify another subsystem's tests to make your code pass.
- Modify specs only with explicit user input; otherwise modify
  implementation to match the spec, or escalate via `/docs/questions.md`.

---

## 4. The OpenSpec Prompt (Ready to Use)

Paste this into OpenSpec (or feed to Claude Code as a one-shot "produce all
deliverables") to generate the architecture doc, per-subsystem specs, zone
outlines, quest catalog, phased build plan, and repository scaffolding plan.

```markdown
# Proposal: Keep on the Borderlands MUD — Open Source Campaign

## Context
Build an open-source persistent multiplayer text MUD that adapts module
B2: The Keep on the Borderlands (Gygax, 1979) as the opening campaign arc.
The implementation will be developed by Claude Code using a Ralph Loop
(iterative spec → test → implement → refine). Spec quality and testability
are therefore first-class concerns, not afterthoughts.

Target: 20-50 concurrent players, accessible via telnet and Evennia's
default web client.

## Locked decisions — do not reopen
- License: open source (recommend MIT or Apache 2.0; propose which)
- Engine: Evennia (Python). Use contribs where they fit: traits, rpsystem,
  combat, clothing, and any others that reduce custom code surface
- Ruleset: Old School Essentials (B/X retroclone). Use the open-license
  SRD text directly where possible. Race-as-class.
- Classes: Cleric, Fighter, Magic-User, Thief, plus race-as-class Dwarf,
  Elf, Halfling per OSE Core Rules
- Level range for B2 content: 1-10 (MUD-scaled from module's 1-3)
- World persistence: seasonal resets. Each season is a campaign cycle
  with persistent character progress but world state advances and resets
- Faction system: scripted faction states (peaceful / tense / war /
  allied) per tribe pair and per player. State transitions triggered by
  scripted thresholds, not full simulation
- Solo viability: hireable henchmen from the Keep (canon to B2). NPCs
  with simple AI that follow, fight, and demand a share of treasure
- Death penalty (default): XP loss to start of current level + corpse
  run to recover gear at death location
- Death penalty (hardcore opt-in): permadeath with a server-wide
  leaderboard tracking highest-level permadeath characters
- PvP: disabled in v1
- Disguised Priest plot: rotating identity tied to seasonal resets. Each
  season a different chapel NPC is the spy; clues are randomly assigned
  from a pool; exposure is per-character, with a server-global "exposed"
  state once any player reports the spy to the Castellan
- Recall point: Inner Bailey of the Keep
- Repop: tribe-scoped. Standard mobs respawn on 15-min timer; killing a
  tribe's chief AND shaman halts that tribe's repop for 60 real minutes
  and triggers a rival tribe's faction state to shift
- Shrine of Evil Chaos: 24-hour reset cycle with server-wide broadcast
- No GM tooling in v1. Re-evaluate after launch.

## Locked architectural patterns
- Spec-test-implement, enforced. Every subsystem (faction, repop, quests,
  combat, henchmen, seasonal reset, disguised Priest, death penalty)
  must have:
  1. A written spec in /docs/specs/<system>.md
  2. A unit test suite in /tests/<system>/ derived from the spec
  3. An implementation that passes those tests
  No implementation work begins on a subsystem before its spec and test
  scaffold exist. This is what makes the Ralph Loop converge.
- Prefer Evennia contribs over custom code; document choices in
  /docs/decisions/
- Type hints everywhere, mypy strict
- One subsystem per commit; commit messages reference the task
- Never modify another subsystem's tests to make your code pass

## Open questions for OpenSpec to propose
- Season length and reset cadence (recommend with reasoning)
- Henchmen mechanics: hiring cost, loyalty/morale rules, share of XP
  and treasure, max number per character, behavior in combat
- Faction state transition thresholds (what player actions move
  kobold-vs-goblin from peaceful to tense to war?)
- Economy: starting gold, shop pricing, banking, gold sinks
- Leaderboard scope: per-season vs all-time vs both
- Whether the Cave of the Unknown is a v1 stub, a v1 mini-zone with
  one author's content, or deferred to a later release
- Web client customization scope (default Evennia client vs themed)
- License choice (MIT vs Apache 2.0 vs AGPL) with reasoning

## Requirements

### R1: Zone structure
Five zones, each its own Python package under /world/zones/:
- keep/ — hub, shops, NPCs, recall, chapel (rotating disguised Priest)
- wilderness/ — overland hex map between Keep and Caves, with module's
  wilderness encounters (hermit, raiders, spider lair, mountain lions)
- caves/ — Caves of Chaos: all humanoid lairs (kobold, two orc tribes,
  goblin, hobgoblin, bugbear, gnoll, ogre, minotaur, owlbear)
- shrine/ — Shrine of Evil Chaos endgame zone
- unknown/ — Cave of the Unknown (scope TBD per open question)

### R2: Faction system (scripted states)
- Each humanoid tribe is a faction. Faction-pair state is one of:
  allied / peaceful / tense / war
- Each (faction, player) standing is one of: friendly / neutral /
  hostile / kill-on-sight
- State transitions are rule-based: e.g., killing 5+ kobolds shifts
  kobold-to-player from neutral to hostile to kill-on-sight; the same
  action shifts kobold-vs-goblin from tense to peaceful
- Initial faction-pair states mirror the module's described politics
- All thresholds and transition rules in a single config file for
  tuning

### R3: Tribe-scoped repop
- Standard mobs: 15-min respawn
- Killing chief AND shaman halts tribe repop for 60 real minutes
- During dead-tribe window, designated rival tribe spawns scouting
  parties into the empty caves; rival's faction-pair state with
  player may shift
- Shrine resets on 24-hour cycle with server broadcast

### R4: Disguised Priest plot (rotating identity)
- At each season start, the spy is randomly assigned to one of N
  chapel NPCs
- Clues assigned from a pool: e.g., "lights candles at midnight,"
  "owns a black-handled dagger," "knows the Shrine's password"
- Spy offers quests that subtly aid the Shrine; completing 3+ of
  them triggers a scripted ambush in the Caves
- Players can detect via: high-level Detect Evil, Curate dialogue
  branch, witnessing a scripted nighttime act, or finding a planted
  object
- Reporting to Castellan triggers server-global "exposed" event;
  spy flees to Shrine and becomes a boss there
- State resets at season boundary

### R5: Henchmen system
- Hire from a roster at the Keep's tavern
- Henchmen are AI-controlled NPCs that follow, fight, and demand
  a share of XP/treasure
- Loyalty/morale per OSE rules; flee or refuse orders below thresholds
- Cap per character (propose number)
- Permadeath for henchmen; replacements must be re-hired

### R6: Seasonal resets
- Season length: TBD (open question)
- At reset: world state (faction states, repop, Shrine, disguised
  Priest identity) resets; player characters, XP, gear, and bank
  persist
- Server broadcasts season transition with narrative framing
- Leaderboard snapshot taken at reset

### R7: Death and hardcore mode
- Default characters: on death, lose XP back to start of current
  level; corpse persists at death location with all gear for retrieval
- Hardcore characters (opt-in at creation, irrevocable): on death,
  character is deleted; final level and season added to leaderboard
- Hardcore characters visually flagged (title, who-list marker)

### R8: Combat
- OSE-faithful: ascending OR descending AC (pick one; recommend
  ascending for player-friendliness), d20 attack rolls, OSE damage,
  OSE saving throws
- Round-based, Evennia ticker-driven
- Vancian spellcasting with memorization on rest

### R9: Quests
- 20-30 quests covering the module
- Givers: Castellan, Curate, Guildmaster, Provisioner, Hermit, tribe
  chiefs (if faction permits), rotating disguised Priest
- Quest state per character; some quests have season-global effects
  (e.g., destroying the Shrine triggers a server event and may end
  the season early)

## Non-goals for v1
- PvP
- GM tooling
- Player housing
- Crafting beyond provisioner purchases
- Content past the Shrine
- Mobile-first UI
- Voice/graphics

## Acceptance criteria (testable)
- A new character can spawn at the Keep, equip from the provisioner,
  hire a henchman, travel to the Caves, complete a tribe-clearing
  quest, and return to turn it in
- Faction state transitions can be triggered by scripted player
  actions in tests and observed in NPC behavior
- Tribe-scoped repop halts and rival-tribe expansion both fire
  correctly under test
- Disguised Priest rotation produces a different identity and clue
  set across two simulated season resets
- Henchmen hire, follow, fight, take treasure share, and refuse
  orders below morale threshold
- Default death applies XP loss and creates retrievable corpse;
  hardcore death deletes character and updates leaderboard
- Season reset clears world state but preserves character data
- Server holds 50 concurrent players with <100ms command latency

## Deliverables OpenSpec should produce
1. Architecture overview (Evennia structure, contrib usage map,
   custom module boundaries, persistence model)
2. Per-subsystem specs in /docs/specs/ for each R1-R9 system
3. Test plan and test stubs in /tests/ for each subsystem
4. Faction system design doc: data model, transition rules, config
   schema, initial values for B2 tribes
5. Zone outlines for all five zones (room counts, mob lists, exits,
   NPC inventory)
6. Quest catalog: giver, prereqs, steps, rewards, faction/season
   effects
7. Henchmen design doc: roster, hire costs, morale/loyalty rules,
   combat AI behavior
8. Seasonal reset spec: cadence recommendation, what persists vs
   what resets, leaderboard mechanics
9. Disguised Priest spec: NPC pool, clue pool, detection paths,
   exposure flow, reset behavior
10. Phased build plan with milestones structured for Ralph Loop
    iteration (smallest-shippable first)
11. Repository scaffolding plan (directory structure, dependency
    list, dev environment setup, CI/test runner)
```

---

## 5. Ralph Loop Strategy

### What a Ralph Loop Is

`while true; do claude < PROMPT.md; done` — Geoffrey Huntley's pattern of
running Claude Code unattended against a stable prompt and a living task
list. The cleverness is in the prompt and the surrounding scaffolding.

### Phase Order

1. **Phase 0 — Generate specs:** Feed the OpenSpec prompt above to
   OpenSpec (or to Claude Code as a one-shot). Commit all deliverables.
   The loop needs specs to converge against.
2. **Phase 1 — Bootstrap the repo manually.** Don't make the loop do
   this. Set up: `evennia --init mygame`, git init, ruff/mypy/pytest
   strict, CI workflow running all three, pre-commit hook, `.claude/`
   config, empty `tasks.md` and `STATUS.md`.
3. **Phase 2 — Generate `tasks.md`** from the phased build plan in the
   OpenSpec output. Each task is one Claude Code session of work
   (~spec → tests → implementation for one subsystem slice). Roughly
   80–150 tasks total. Checkboxes so progress is grep-able.
4. **Phase 3 — Write PROMPT.md** (template below).
5. **Phase 4 — Run the loop** in a tmux session.
6. **Phase 5 — Review every few hours** or whenever STATUS.md appears.
   Read commits, skim diffs, check `questions.md`, update specs/tasks,
   restart.

### Build Order (for Ralph-friendliness)

Maximize early integration to surface architectural bugs before they
compound:

1. Repo scaffolding tasks
2. Core combat (smallest testable system)
3. Faction state machine
4. Henchmen
5. Repop and seasonal reset
6. Keep zone
7. Wilderness zone
8. **One cave (kobolds) end-to-end as a vertical slice** — critical;
   surfaces every integration bug before you've built nine more caves
   the same way
9. Remaining caves
10. Shrine
11. Disguised Priest
12. Quest catalog
13. Polish

### PROMPT.md Template (Drop at Repo Root)

```markdown
# Ralph Loop: Keep on the Borderlands MUD

You are building this project iteratively. Each invocation, do ONE task.

## Workflow
1. Read /docs/specs/ to understand the architecture
2. Read /tasks.md and pick the first unchecked task
3. If the task requires a spec that doesn't exist, write the spec first
   in /docs/specs/<system>.md and stop. Mark task progress, commit, exit.
4. If the spec exists but tests don't, write the test suite in
   /tests/<system>/ derived from the spec. Stop. Commit. Exit.
5. If tests exist but fail or are missing implementation, implement
   until all tests pass. Then commit. Exit.
6. Before any commit: run `pytest`, `mypy --strict`, `ruff check`.
   If any fail, fix before committing. Do not commit red.
7. Mark the task complete in /tasks.md if and only if the full
   spec→test→implementation cycle for it is done and green.

## Conventions
- Evennia contribs preferred over custom code; document choices in
  /docs/decisions/
- Type hints everywhere, mypy strict
- One subsystem per commit; commit messages reference the task
- Never modify another subsystem's tests to make your code pass

## Stop conditions
- If /tasks.md is fully checked, write "RALPH: project complete"
  to /STATUS.md and exit
- If you encounter a decision not covered by specs, write the
  question to /docs/questions.md and exit without committing code
- If tests have been red for 3 consecutive commits on the same task,
  write to /STATUS.md and exit for human review

## Important
- Do not invent requirements not in the specs
- Do not skip the spec or test phase to get to implementation faster
- Do not modify /docs/specs/ to match your implementation; modify
  the implementation to match the spec, or escalate via /docs/questions.md
```

### Loop Runner Script

```bash
#!/usr/bin/env bash
set -u
while true; do
  claude -p --dangerously-skip-permissions < PROMPT.md
  sleep 30
  if [ -f STATUS.md ]; then
    echo "STATUS.md appeared:"
    cat STATUS.md
    break
  fi
done
```

Run in tmux, expect to babysit periodically.

### Operational Tips (Hard-Earned)

- **Use a worktree or dedicated branch.** Be able to nuke loop output
  without losing bootstrap. `git worktree add ../mud-ralph ralph-branch`.
- **Hard quality gates are the safety net.** Strict mypy, ruff, real
  tests. If CI takes >60s, the loop will outrun your ability to review.
- **Token cost is real.** Set a budget, monitor in the Anthropic
  console, use prompt caching (keep spec files at stable paths so
  they cache).
- **"Stuck on red" stop condition is the most important.** Without
  it, the loop spends hours and hundreds of dollars thrashing on a
  test it can't pass. The 3-commits-red rule forces intervention.
- **Use a verification subagent on gnarly subsystems** (faction state
  machine, seasonal reset, rotating Priest). Have the main loop spawn
  a subagent that reviews implementation against spec independently.
- **The loop is a builder, not an architect.** If `questions.md` grows
  fast, the specs are too thin — stop, expand, restart.

---

## 6. Container Setup (Linux Host)

Run the Ralph Loop inside Podman (or Docker — equivalent for this use
case) so `--dangerously-skip-permissions` is bounded.

**Linux-specific advantages over the earlier macOS plan:**
- No `podman machine` / Docker Desktop VM needed; containers run
  natively at near-host speed.
- Rootless Podman is fully supported out of the box.
- Direct bind mounts — no file-sharing performance penalty.
- Either Podman or Docker via the distro's package manager works
  identically for this purpose. Podman has marginal edge for safety
  (rootless default), Docker has marginal edge for ecosystem
  familiarity. Pick whichever you already use.

### Architecture: Hybrid

- **Interactive dev on host:** Edit files in your IDE, run quick
  smoke tests directly.
- **Ralph Loop inside container** with `--dangerously-skip-permissions`.
  Container has only the project directory mounted and outbound
  network for `pip` / `git push` / Claude API.

### Containerfile (Sketch)

```dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl tmux ca-certificates build-essential \
 && rm -rf /var/lib/apt/lists/*

# Install Claude Code (verify exact install command at build time;
# Anthropic ships an installer for Linux)
RUN curl -fsSL https://claude.ai/install.sh | sh    # placeholder — verify

# Project tools
RUN pip install --no-cache-dir \
    evennia \
    pytest pytest-django pytest-cov \
    mypy ruff \
    pre-commit

WORKDIR /workspace
CMD ["bash"]
```

### Run Command

```bash
podman run --rm -it \
  --name kotb-ralph \
  -v ~/Projects/keep-on-borderlands:/workspace:Z \
  -e ANTHROPIC_API_KEY \
  kotb-ralph:latest \
  bash -c 'cd /workspace && ./scripts/ralph.sh'
```

The `:Z` SELinux relabel is fine on Fedora/RHEL; drop it on Debian/Ubuntu.

### Network Hardening (Optional, Recommended Later)

Once the loop is stable, restrict outbound network to just the Claude
API endpoint and your git remote. Use `--network` with a custom Podman
network or run behind a transparent proxy. Not v1, but worth knowing.

---

## 7. Bootstrap Checklist (Run Once on Linux)

```bash
# 1. Create project dir (already exists at ~/Projects/keep-on-borderlands)
cd ~/Projects/keep-on-borderlands

# 2. Git init
git init
git branch -m main

# 3. Initial directory structure
mkdir -p docs/specs docs/decisions docs/research \
         tests world/zones scripts .github/workflows

# 4. Drop in core files:
#    - CLAUDE.md (this file)
#    - PROMPT.md (Ralph Loop prompt — Section 5 template above)
#    - tasks.md (generated from OpenSpec phased build plan)
#    - STATUS.md (empty placeholder)
#    - docs/questions.md (empty placeholder)
#    - .gitignore (Python + Evennia standard)
#    - pyproject.toml with ruff/mypy/pytest config
#    - .pre-commit-config.yaml
#    - .github/workflows/ci.yml running ruff, mypy --strict, pytest
#    - Containerfile (from Section 6)
#    - scripts/ralph.sh (loop runner from Section 5)

# 5. Evennia scaffold
pip install evennia
evennia --init mudgame
# Or inside container; mudgame/ becomes the Evennia game directory.

# 6. First commit
git add -A
git commit -m "Initial scaffolding"

# 7. Generate specs via OpenSpec (feed Section 4 prompt)
#    Commit the generated /docs/specs/, /docs/architecture.md, etc.

# 8. Generate /tasks.md from the phased build plan

# 9. Build the container
podman build -t kotb-ralph -f Containerfile .

# 10. Start the loop
podman run --rm -it \
  -v $(pwd):/workspace:Z \
  -e ANTHROPIC_API_KEY \
  kotb-ralph \
  bash -c 'cd /workspace && ./scripts/ralph.sh'
```

---

## 8. Open Questions (Defer to OpenSpec / First Pass)

These were intentionally deferred. OpenSpec should propose answers with
reasoning; the user makes final calls.

- License: MIT vs Apache 2.0 vs AGPL
- Season length and reset cadence
- Henchmen specifics: hire cost curve, cap per character, behavior in
  combat
- Faction state transition thresholds (concrete numbers)
- Economy: starting gold, shop pricing, gold sinks
- Leaderboard scope: per-season, all-time, or both
- Cave of the Unknown: v1 stub, v1 mini-zone, or deferred
- Web client customization scope
- AC convention: ascending (player-friendly) vs descending (period-
  authentic). Default recommendation: ascending.

---

## 9. Things Considered and Rejected

Captured so future-Claude doesn't re-litigate.

- **ROM / Diku C codebase.** Rejected: dev velocity disaster with
  Claude as builder.
- **CoffeeMUD (Java).** Worth a look but Evennia's Python ecosystem
  is a better fit for Claude Code maintenance.
- **Custom MUD from scratch in Rust/Go.** Always tempting, almost
  always wrong. Rejected.
- **AD&D 1e rules.** Rejected: B2 was written for B/X; 1e tripled
  the rule surface for no real fidelity gain.
- **Emergent simulated factions** (tribes have AI goals, simulate
  on a tick). Rejected for v1: too much code, too many bug surfaces
  for a Ralph Loop. Scripted states are the testable middle ground.
- **Standard Diku 15-min total repop.** Rejected: kills the political
  layer that makes B2 worth adapting.
- **Per-player instancing of the disguised Priest.** Rejected: breaks
  shared-world illusion.
- **PvP in v1.** Deferred: complexity vs payoff doesn't pencil at
  this scale.
- **Forced grouping.** Rejected: kills MUDs at low population.
  Henchmen solve the problem.

---

## 10. Quick-Start for a Fresh Claude Session

If you (Claude) are reading this cold:

1. Read this file end-to-end. Decisions in Section 2 and patterns in
   Section 3 are locked.
2. Check `/docs/specs/` for what's been generated.
3. Check `/tasks.md` for current state.
4. Check `/docs/questions.md` for anything blocking.
5. Check `/STATUS.md` for last-loop-exit reason.
6. If specs don't exist yet, run the OpenSpec prompt (Section 4).
7. If `tasks.md` doesn't exist yet, generate from the phased build
   plan in the OpenSpec output.
8. If both exist, you can start the loop, or pick the next task and
   work it manually.
9. When in doubt, ask the user — don't invent requirements.
