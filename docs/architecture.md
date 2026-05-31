# Architecture Overview — Keep on the Borderlands MUD

This is the canonical architecture for the v1 implementation. It fixes the
Evennia package layout, the contrib usage map, the boundaries between custom
modules, the persistence model, and the cross-cutting rules conventions every
subsystem spec depends on. Subsystem specs (`docs/specs/*.md`) refine the
*behavior* of each system; this document fixes the *structure* they all share.

Locked decisions live in `CLAUDE.md` §2–§3 and ADRs `0001`–`0003`. This doc does
not reopen them; it operationalizes them.

---

## 1. Engine and game directory

The game runs on **Evennia** (Python 3.12, Django ORM, Twisted). Phase 1 creates
the game directory with `evennia --init mudgame`. All custom code lives under
`mudgame/`; the name is already reserved (it is `extend-exclude`d from ruff in
`pyproject.toml` because Evennia's generated scaffold is treated as vendored).

```
mudgame/                      # Evennia game directory (created in Phase 1)
├── server/
│   └── conf/
│       ├── settings.py       # Evennia + Django settings; ticker config
│       └── at_initial_setup.py   # builds the world + spins up GlobalScripts
├── commands/
│   ├── default_cmdsets.py    # wires custom cmdsets onto Character/Account
│   ├── combat.py             # attack, cast, flee, ...
│   ├── factions.py           # consider, standing
│   ├── henchmen.py           # hire, dismiss, order, give-share
│   └── quests.py             # quest, journal, turnin
├── typeclasses/
│   ├── characters.py         # PlayerCharacter
│   ├── npcs.py               # NPC base, Mob, Henchman, ChapelNPC
│   ├── rooms.py              # Room (+ extended_room behaviors)
│   ├── exits.py
│   ├── objects.py            # Item, Weapon, Armor, Corpse, ClueObject
│   └── scripts.py            # ticker + global-script typeclasses
└── world/
    ├── rules/                # pure OSE rule tables + dice (engine-agnostic)
    │   ├── ose_tables.py     # saves, XP thresholds, attack bonus, morale
    │   ├── classes.py        # class/race-class definitions
    │   ├── spells.py         # Vancian spell lists + effects
    │   └── dice.py           # d20 / xdy helpers
    ├── factions/
    │   └── config.py         # THE single faction tuning file (R2)
    ├── managers/             # global persistent Scripts (singletons)
    │   ├── faction_manager.py
    │   ├── repop_manager.py
    │   ├── season_manager.py
    │   └── priest_manager.py
    └── zones/                # one package per zone (R1)
        ├── keep/
        ├── wilderness/
        ├── caves/
        ├── shrine/
        └── unknown/
```

The two `world/` sublayers are deliberately separated:

- **`world/rules/`** is pure Python — no Evennia imports. OSE math (to-hit,
  saving throws, XP, morale) is the most test-dense surface in the project, and
  keeping it import-free means its unit tests run without booting Evennia/Django.
  This is the single most important testability decision in the architecture.
- **`world/managers/`** holds the stateful, Evennia-coupled singletons. They
  call into `world/rules/` for math but own all persistence and scheduling.

---

## 2. Contrib usage map

CLAUDE.md §3 mandates: *prefer Evennia contribs over custom code; document every
contrib used and every contrib rejected in favor of custom code.* This is that
record. (Exact import paths are verified during Phase 1 against the installed
Evennia version; the package groupings below reflect Evennia's current
`evennia.contrib.{rpg,game_systems,grid,base_systems,tutorials}` layout.)

### Adopted

| Contrib | Used for | Notes |
|---|---|---|
| `rpg.traits` | All OSE numeric state: STR/INT/WIS/DEX/CON/CHA, HP, AC, attack bonus, saving throws, XP, level, encumbrance | `TraitHandler` on Character/NPC. Static traits for scores, counter traits for HP, gauge where a max matters. |
| `rpg.rpsystem` | `sdesc`/`recog` short descriptions and emotes | **Load-bearing for the disguised priest (R4):** players see "a hooded acolyte" until they `recog` (identify) the spy. Also covers the project's roleplay surface. |
| `game_systems.clothing` | Worn equipment layering; armor that contributes to AC | Armor objects set an AC contribution consumed by the combat AC calculation. |
| `grid.extended_room` | Time-of-day / season-aware room descriptions and searchable `details` | Enables the day/night cycle the priest plot needs ("lights candles at midnight") and richer B2 room text. |
| `grid.xyzgrid` | The Wilderness overland map (R1) | Coordinate-addressable rooms model the module's wilderness hexes; supports map rendering in the web client. |
| `rpg.buffs` | Timed spell/condition effects (bless, light, hold, protection) | Durations expire on the combat/round ticker. |
| `rpg.character_creator` + core `EvMenu` | Menu-driven character creation; NPC dialogue trees (Curate, Castellan, priest) | Hardcore opt-in (R7) and class/race-class selection happen here. |

### Adopted-as-pattern (lifted, not imported verbatim)

| Contrib | Why not verbatim |
|---|---|
| `game_systems.turnbattle` (e.g. the `tb_magic` variant) | Evennia ships a *turn-based combat example*, not a drop-in OSE engine. We lift its ticker/turn-handler structure and command shape, but the rules core (initiative, attack resolution, damage, saves, morale) is custom in `world/rules/` because it must be OSE-faithful and heavily unit-tested. Documented as a deliberate "contrib-inspired, custom implementation." |
| core `TICKER_HANDLER` | Used directly for round timing and repop timers — it is core, not a contrib, but called out because R3/R8 depend on it. |

### Rejected

| Contrib | Why rejected |
|---|---|
| `game_systems.crafting` | Crafting beyond provisioner purchases is a v1 non-goal. |
| `game_systems.barter` | PvP is disabled in v1; the provisioner is a simple buy/sell shop, not player-to-player barter. |
| `grid.wilderness` (procedural) | The B2 wilderness is *authored*, not procedural. `xyzgrid` (fixed coordinate rooms) fits the hand-built hex map; the procedural `wilderness` contrib would discard the module's set-piece encounters. |
| `game_systems.mail`, `tutorials.*` | Out of scope / example content. |

Every adoption/rejection above is restated in the relevant subsystem spec where
it bites, and any reversal during implementation must be logged in
`docs/decisions/` per CLAUDE.md §3.

---

## 3. Custom module boundaries

| Layer | Package | Owns | Must NOT |
|---|---|---|---|
| Rules core | `world/rules/` | OSE math, tables, dice, spell data | import Evennia/Django; hold state |
| Static content | `world/zones/<zone>/` | Room/exit/mob/NPC/item data as plain data structures | contain behavior beyond simple builder hooks |
| Config | `world/factions/config.py` | All faction-pair initial states + transition thresholds (R2) | be edited by code at runtime (it is tuning input) |
| Managers | `world/managers/` | Global mutable world state + scheduling (factions, repop, season, priest) | duplicate rules math (call `world/rules/`) |
| Typeclasses | `typeclasses/` | Entity behavior bound to persistence (Character, Mob, Henchman, Corpse, Room) | hardcode tuning numbers (read from rules/config) |
| Commands | `commands/` | Player-facing verbs + cmdsets | contain rules math or world state |

The dependency direction is strict and acyclic:
`commands → typeclasses → managers → rules/config`, with `zones` providing data
consumed by the world builder. Tests assert against `rules`/`config` directly
and against managers via Evennia's test harness.

---

## 4. Persistence model

CLAUDE.md §3: *Django ORM for player and world state; flat files only for static
area definitions.* Concretely:

| Data | Home | Survives seasonal reset? |
|---|---|---|
| Player character (level, XP, gear, bank, hardcore flag, quest journal) | Character typeclass Attributes (`.db`) + Account | **Yes** (R6) |
| Faction-pair states & per-player standings | `faction_manager` GlobalScript Attributes | No — reset |
| Repop timers / dead-tribe windows | `repop_manager` GlobalScript Attributes | No — reset |
| Season number, phase, narrative state | `season_manager` GlobalScript Attributes | Number persists; world state resets |
| Disguised-priest identity, clue assignment, exposure flag | `priest_manager` GlobalScript Attributes | No — re-rolled each season |
| Leaderboard entries | dedicated rows (small Django model or a persistent global Script list) | **Yes** (append-only) |
| Static room/mob/item definitions | flat Python in `world/zones/` | n/a (source, not state) |
| Live room/mob instances | Evennia objects in the DB, (re)built from zone data | No — rebuilt on reset/repop |

**Global state pattern.** The four managers are Evennia *persistent global
Scripts* (singletons created in `at_initial_setup`, retrieved by key). This keeps
world state queryable, automatically persisted, and tick-capable without a custom
storage layer. The seasonal reset (R6) is, mechanically, "flush manager state and
re-run the relevant parts of the world build" — see `docs/specs/seasonal-reset.md`.

**Corpses** (R7) are ordinary persistent objects placed at the death room with
the player's gear moved into them, plus a decay timer; no special storage.

---

## 5. Cross-cutting rules conventions

### 5.1 Armor Class — ascending (AAC)

**Decision: ascending AC.** Resolves the open question in CLAUDE.md §8 in favor
of the §8 default.

- Unarmored AC = **10**. Higher is better.
- To-hit: `d20 + attack_bonus + STR/DEX_mod + situational ≥ target_AAC` → hit.
- `attack_bonus` is the class/level value (OSE's ascending "attack bonus" column,
  equivalent to `THAC0` reframed as `attack_bonus = 20 − THAC0`).
- Conversion from any descending-AC source text: `AAC = 19 − descending_AC`.

Rationale: a single comparison (`roll + bonus ≥ AC`) is easier to implement,
read, and unit-test than THAC0 subtraction; it matches modern player
expectations; and OSE itself publishes ascending values, so no homebrew is
introduced. Descending AC is recorded in zone source comments only as a
provenance note.

### 5.2 Dice, rounds, and time

- All randomness flows through `world/rules/dice.py` so tests can seed/patch it.
- Combat is **round-based**, driven by Evennia's `TICKER_HANDLER`; the canonical
  round length and initiative model are fixed in `docs/specs/combat.md`.
- A **day/night clock** (game time via Evennia's gametime utilities, surfaced
  through `extended_room`) drives the priest's nighttime acts (R4) and any
  time-gated room text. Real-time timers (15-min repop, 60-min halt, 24-h Shrine)
  use wall-clock scheduling, not game time — see `docs/specs/repop.md`.

### 5.3 Identity and naming

Subsystem specs and zone outlines share a single vocabulary for tribes, NPCs,
and zones. The faction roster in `docs/specs/faction.md` §"B2 tribes" is the
source of truth for tribe identifiers; zone outlines and the quest catalog refer
to those identifiers verbatim to keep the corpus internally consistent.

---

## 6. Testability contract

Per CLAUDE.md §3 every subsystem ships spec → tests → implementation in that
order. This architecture makes that tractable:

- **Pure rules** (`world/rules/`) are tested with plain pytest, no Evennia boot.
- **Managers and typeclasses** are tested with Evennia's `EvenniaTest`
  base class (Django test DB), seeding manager state and asserting transitions.
- **Each OpenSpec scenario** in `openspec/changes/b2-mud-v1-design/specs/<cap>/`
  maps to at least one test in `tests/<system>/`. Phase 0 ships those tests as
  skipped stubs; Phase 2 unskips and implements them.

See `docs/specs/scaffolding.md` for the directory/dependency/CI plan and
`docs/build-plan.md` for the order in which these layers are built.
