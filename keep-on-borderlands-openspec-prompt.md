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
- Prefer Evennia contribs over custom code. Document any contrib used
  and why; document any case where a contrib was rejected and custom
  code written instead.
- Type hints + mypy strict mode on all custom modules.
- Modular zone files. Each zone is its own Python package, not a
  monolithic data file.
- Use Django ORM (Evennia's persistence layer) for player and world
  state; flat files only for static area definitions.

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
