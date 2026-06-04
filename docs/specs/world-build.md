# World-Build Spec (M15) — runtime world bring-up orchestrator

The phase the deferrals have been pointing at: a runtime orchestrator that makes
the game **actually run a populated world**. Today every zone's `build()` creates
rooms, exits, and static NPCs, but **no mob is ever instantiated** — the
`repop_manager._instantiate` spawner and `season_manager.rebuild_world` are
deliberate logged no-ops (architecture §4; `tasks.md` "World-build / runtime
orchestrator"). This spec defines the layer that replaces those no-ops, wires
quest-givers by an explicit key (M13 F1), installs the world-event hooks that set
deed-completion flags (M13 F3), and exposes a bootable, load-testable server.

This is the **structural + behavioral** spec for the orchestrator; it does not
reopen any locked decision (CLAUDE.md §2–§3) and it does not author new content —
it instantiates the content the zone packages already define. Per `PROMPT.md`,
this turn writes the spec only; tests (`tests/world_build/`) and implementation
follow in later milestone slices after the M15 spec-review gate.

Testable contract is §13; the test plan is §14.

---

## 1. Scope and non-goals

**In scope (M15):**

1. A single boot orchestrator that builds every zone in dependency order, ensures
   the four global managers exist, registers each zone's spawn points, and runs
   an **initial population pass** so a freshly-booted server has live mobs/leaders
   standing in their rooms.
2. A **mob spawner** that turns a `MobRecord` template + a target room into a live
   `Mob` typeclass instance with OSE stats, faction, leader role, and `spawn_id`
   wired — replacing the `repop_manager._instantiate` / `_instantiate_scout`
   no-ops and `season_manager.rebuild_world`.
3. **Quest-giver resolution by explicit giver-key** (M13 review F1): givers
   (Guildmaster, Castellan, Curate, Provisioner, Hermit, tribe chiefs, the
   rotating spy) are reachable for `quest`/`accept`/`turnin` regardless of their
   display `role`.
4. **World-event deed hooks** (M13 review F3): the triggers that call
   `world.quests.state.record_deed` for deed-only quests (shrine destroyed,
   rations delivered, captive escorted, spy package delivered).
5. A **bootable, load-testable server**: a documented headless build entry point
   and a population/latency harness sketch that unblocks the three deferred M14
   acceptance criteria (economy/XP balance, 50-player <100 ms latency, full
   acceptance verification).

**Out of scope (explicit non-goals):**

- No new zones, rooms, mobs, NPCs, quests, or tuning numbers — content is frozen
  at M13/M11 levels; M15 only brings it to life.
- No change to the pure rules core (`world/rules/`) or to any locked decision.
- The M14 *measurements* themselves (running the load harness, recording latency,
  balancing the economy from playtest data) are unblocked by M15 but tracked as
  their own M14 tasks; M15 delivers the runnable server they need, not the
  numbers.
- No GM tooling (CLAUDE.md §2: "No GM tooling in v1").

---

## 2. The seam today (what M15 replaces)

| Today (no-op) | Replaced by |
|---|---|
| `repop_manager._instantiate(point)` — logs, clears timer, spawns nothing | spawner instantiates the mob from its template at its room |
| `repop_manager._instantiate_scout(scout)` — logs only | spawner instantiates a rival scout in the broken tribe's lair |
| `repop_manager._retreat_scout(scout)` — logs only | spawner despawns the live scout instance |
| `repop_manager._reset_shrine` restock loop — rides the no-op `_instantiate` | same spawner path; Shrine restock now produces live cult mobs |
| `season_manager.rebuild_world()` — logs "no-op pre-M7" | calls the orchestrator's rebuild entry point |
| `commands.quests._giver_here` — matches `db.role in GIVERS` (only Guildmaster/Castellan resolve) | matches an explicit `db.giver_key in GIVERS` set on every giver |
| deed-completion flags (`record_deed`) — no world event ever calls it | world-event hooks (§9) call it on the real in-world trigger |

The registries the spawner reads **already exist and are tested**: zone
`MOB_TEMPLATES`/`SPAWNS` (zones spec), the `repop_manager` spawn-point registry
(`spawn_registry.spawn_points`), and the pure `RepopState` timers. M15 supplies
the missing *materialization* of those records into Evennia objects.

---

## 3. Package layout

A new Evennia-coupled package, parallel to `world/zones/builder.py`:

```
world/build/
├── __init__.py        # exposes build_all() and rebuild_world()
├── orchestrator.py    # build_all(): zone build order + manager bring-up + initial spawn
├── spawner.py         # spawn_mob(), spawn_scout(), despawn(): MobRecord -> live Mob
├── templates.py       # mob-template registry: template_key -> MobRecord (pure)
└── events.py          # world-event deed hooks (§9): record_deed triggers
```

- `templates.py` is **pure** (no Evennia import) — it aggregates every zone's
  `MOB_TEMPLATES` into one `template_key -> MobRecord` map, so the lookup is
  unit-testable without booting the server (mirrors `spawn_registry`'s purity).
- `orchestrator.py`, `spawner.py`, `events.py` import Evennia lazily (inside
  functions), so importing the package stays Django-free for pure tests — the
  same discipline every `build.py` already follows.
- `repop_manager._instantiate*` and `season_manager.rebuild_world` become thin
  delegators into `world.build.spawner` / `world.build.orchestrator`. The
  managers keep owning timers/state; the build package owns materialization. This
  preserves the architecture §3 dependency direction
  (`managers → build → zones/rules`); the build package must **not** import the
  command layer.

---

## 4. The boot orchestrator — `build_all()`

`world.build.orchestrator.build_all()` is the single entry point invoked from
`server/conf/at_initial_setup.py` at first boot (replacing the empty
`at_initial_setup()` body). It is **idempotent** end-to-end — safe to re-run on
every boot and from the season rebuild — and proceeds in dependency order:

1. **Ensure managers.** Create the four global Scripts
   (`faction_manager`, `repop_manager`, `season_manager`, `priest_manager`) if
   absent, retrieve-by-key if present. Managers must exist before zone builds so
   `register_zone` and the priest pool tagging land.
2. **Build zones in order:** `keep` → `wilderness` → `caves` → `shrine` →
   `unknown`. Order matters for inter-zone exits (the Keep↔Wilderness south exit
   is deferred until `wilderness:keep_road` is tagged — wilderness spec §6) and so
   the recall point and priest pool exist before later wiring. Each zone's
   existing `build()` is called unchanged; M15 adds nothing to zone `build()`
   beyond the new `giver_key` field (§8) flowing through the builder.
3. **Register spawns.** Each cave tribe's `build()` already calls
   `register_zone`; the orchestrator additionally registers any zone whose
   `build()` does not (Keep service mobs, Shrine cult, Wilderness set-pieces) so
   every `SPAWNS` record is known to the `repop_manager`.
4. **Initial population pass.** After all spawns are registered, the orchestrator
   asks the spawner to instantiate **one live mob per registered spawn point that
   has no live instance yet** (§6 idempotency). This is what makes the booted
   world populated rather than empty. Leaders (`is_leader`, `leader_role`) are
   spawned here too, so the M6 leadership-halt + scouting paths have real targets.
5. **Arm cycles.** The Shrine 24h reset cycle and any other manager timers arm
   via their existing `at_repeat`/reset hooks; the orchestrator does not
   duplicate that logic.

`build_all()` returns a small summary (counts of rooms, exits, NPCs, mobs built)
for the boot log and for the test harness to assert against.

---

## 5. Mob-template registry — `templates.py`

The spawner is handed a `SpawnPoint` (or a `Scout`), which carries the
**template key** and the **room tag** but not the stat block. It needs the full
`MobRecord`. `templates.py` provides:

- `all_templates() -> dict[str, MobRecord]` — aggregates `MOB_TEMPLATES` from every
  zone package (Keep, Wilderness, each cave tribe, Shrine). Built by importing the
  pure data modules only (no `build.py`), so it stays Evennia-free.
- `get_template(key: str) -> MobRecord` — raises `KeyError` on an unknown key,
  matching the integrity `spawn_registry.spawn_points` already enforces.

**Invariant:** template keys are globally unique across zones. The registry build
raises on a duplicate key (a build-time integrity error surfaced by a test in
`tests/world_build/`), keeping the `spawn_id` namespace (`<zone>:<room>:<template>:<n>`)
unambiguous.

---

## 6. The mob spawner — `spawner.py`

`spawn_mob(point: SpawnPoint, *, rng=None) -> Mob | None` is the core replacement
for `repop_manager._instantiate`. It:

1. Resolves the live room by tag (`search_object_by_tag(point.room, ROOM_CATEGORY)`
   — the same identity the builder writes). Returns `None` (logged) if the room is
   not built yet, mirroring the deferred-target handling in `build_exits` so a
   partial world never crashes the tick.
2. Looks up the `MobRecord` via `templates.get_template(point.mob_template)`.
3. Creates a `Mob` typeclass instance (`typeclasses.npcs.Mob`) in that room and
   sets its traits/attributes **from the record**, reusing the existing trait
   schema (`Mob.at_object_creation`):
   - `ac` ← `record["ac"]` (ascending AC, architecture §5.1);
   - `hp` (gauge base+current) ← rolled from `record["hd"]` via
     `world.rules.dice.roll`, threaded through the **seeded RNG seam** so tests are
     deterministic (architecture §5.2); `level`, `morale` from the record;
   - `attack_bonus` derived from `level`/`hd` per the OSE table in
     `world/rules/` (no new math — read existing tables);
   - `db.faction_id` ← `record["faction"]`; `db.is_leader` ← `point.is_leader`;
   - `db.spawn_id` ← `point.spawn_id` — the back-reference that makes the mob's
     death report to the `repop_manager` (`Mob._report_death_to_repop`).
4. Sets `db.giver_key` when the template names a quest-giving chief (§8).
5. Returns the live mob (or `None`). The caller (`repop_manager`) clears the
   timer regardless, so a missing room/template never wedges the registry — the
   exact safety property the no-op preserved.

**`spawn_scout(scout: Scout, *, rng=None)`** instantiates a rival-tribe scout the
same way (its `MobRecord` comes from the rival faction's template set), placed in
the broken tribe's lair room; it carries the scout's id so
`notify_scout_death` resolves it. **`despawn(spawn_id | scout_id)`** finds the
live instance by its instance tag (§7) and deletes it — used by `_retreat_scout`
and by any rebuild that must clear stale instances first.

The `repop_manager` keeps owning *when* to spawn (timers, halt windows, the 24h
Shrine cycle); the spawner owns *how*. `_instantiate`, `_instantiate_scout`,
`_retreat_scout`, and `_reset_shrine`'s restock loop become one-line delegations.

---

## 7. Instance identity and idempotency

To stay idempotent across re-boots and season rebuilds, a live spawned mob is
tagged with a **spawn-instance tag** `point.spawn_id` in a dedicated category
(`spawn_instance`). The spawner:

- before creating, searches for an existing instance of that `spawn_id`; if one is
  alive it **skips** (no duplicate) — so the initial population pass and a repop
  tick converge to "exactly one live mob per due point";
- on death/retreat/reset, the instance is removed and the tag frees up, so the
  next due respawn re-creates it.

This makes `build_all()` runnable on every boot (not just first boot) without
piling up duplicate mobs, and makes the season rebuild "despawn stale instances →
re-spawn from registry" a clean, testable cycle.

---

## 8. Quest-giver wiring by explicit giver-key (M13 review F1)

Today `commands.quests._giver_here` matches an NPC by `db.role in GIVERS`, but
`role` is a **display descriptor** for most NPCs (the spy's chapel role is
`almoner`/etc., the hermit, the provisioner) — only the Guildmaster and Castellan
happen to have `role == giver-key`, so the Hermit/Provisioner/spy and the
tribe-chief givers are unreachable.

**Fix — a giver-key separate from display role:**

1. Add an optional `giver_key: str` to `NpcRecord` and `MobRecord` (records.py).
   It holds the stable quest-giver id from `world.quests.config.GIVERS`
   (`guildmaster`, `castellan`, `curate`, `provisioner`, `mad_hermit`,
   `orc_vol_chief`, `orc_dec_chief`, `goblin_chief`, and the `spy` sentinel).
2. `builder.build_npcs` writes `record["giver_key"]` to `npc.db.giver_key`; the
   spawner (§6) writes `record["giver_key"]` to `mob.db.giver_key` for chief
   givers. `db.role` keeps its display meaning untouched.
3. `commands.quests._giver_here` resolves on `db.giver_key in GIVERS` instead of
   `db.role`. The spy is resolved through the `priest_manager` (the live spy NPC
   this season carries `giver_key == "spy"` once assigned).

**Tribe-chief turn-in design (the "a chief you may also be there to kill"
question).** A tribe chief is both a kill target and a quest giver, so:

- A chief's giver quests target a **rival** faction (the playable orc-vs-orc
  rivalry, faction spec) — you clear his enemy, not him.
- Listing/accepting/turning-in a chief quest requires the chief to be **alive and
  present** (resolved by `giver_key` on the live mob). If the chief is dead (killed
  or under a leadership halt), his quests are simply unavailable until he respawns
  (repop spec) — no corpse turn-in, no proxy. This needs no new state: it falls
  out of giver presence.
- Killing your patron chief forfeits nothing already turned in; an *accepted but
  not turned-in* chief quest stays in the journal and becomes turn-in-able again
  when he respawns. This is the least-surprising rule and adds no special-casing.

---

## 9. World-event deed hooks (M13 review F3)

M13 closed the deed-quest turn-in exploit: a deed-only quest's turn-in is gated on
`QuestEntry.deed_done`, set only by `world.quests.state.record_deed`. The world
events that *call* `record_deed` were deferred to the runtime layer — they are
M15's job. `world.build.events` defines one hook per deed; each finds the relevant
character's quest log and calls `record_deed`:

| Deed quest | World trigger (M15 hook) |
|---|---|
| destroy the Shrine (`c_destroy_shrine`) | `Altar.at_destruction` already fires `end_season` (the canonical R6 trigger, M13 F4); the hook **additionally** sets the shrine-destroyed deed flag so turn-in grants only the reward. It must **not** re-fire `end_season`. |
| deliver rations / supplies | arrival of the carried delivery item at the destination room (or a `give` to the target NPC) sets the deed for the carrier. |
| escort captive home | the escorted NPC reaching the Keep (recall/arrival hook) sets the deed for the escorting player. |
| spy package drop-off (priest chain) | delivering the spy's package at the drop sets the deed; ties into the priest-plot ambush chain (disguised-priest spec). |

Design rules:

- Hooks live in `world.build.events` and are called from the in-world object/room
  behavior (the altar, the delivery item, the escort NPC). The behavior imports
  the hook lazily; the hook imports `world.quests.state` (pure) — no command-layer
  dependency.
- A hook is a **no-op for any character without that quest accepted** — it never
  errors on the common case, mirroring the defensive style of the existing kill
  credit (`Mob._credit_quest_kill`).
- The completion *effects* (`tension_pair`/`aid_faction`/`breaks_alliance`/cult
  chain/`reward.items`) are already wired and tested at the wiring level in
  `tests/quests`; M15 only supplies the trigger that flips `deed_done`.

---

## 10. Season rebuild integration

`season_manager.rebuild_world()` (today a no-op) delegates to
`world.build.orchestrator.rebuild_world()`, which:

1. Despawns stale live mob/scout instances (§7) for zones that reset, then
2. re-runs the zone `build()` hooks (idempotent — rooms/exits/NPCs update in
   place) and the initial population pass.

This realizes the architecture §4 statement that seasonal reset is mechanically
"flush manager state and re-run the relevant parts of the world build"
(seasonal-reset spec). The reset *ordering* is unchanged — `season_manager`
already calls `reset_factions`/`reset_repop`/`reset_priest`/`reset_shrine`/
`revert_season_quests` then `rebuild_world`/`refresh_roster`; M15 only makes the
last two do real work. Player-persisted state (characters, XP, gear, bank,
leaderboard) is untouched by the rebuild (architecture §4; R6).

---

## 11. Boot and load-testability

The third deliverable is a server that can actually be stood up and load-tested,
unblocking the deferred M14 criteria.

- **Boot entry point.** `at_initial_setup()` calls `build_all()`. A documented
  management path (an Evennia `@batchcommand` or a `build` admin command, decided
  at implementation per the Evennia version) lets an operator (re)build the world
  on an existing DB without a fresh `--init`. The path must be idempotent (§7).
- **Headless population check.** The test harness boots the Evennia test server,
  runs `build_all()`, and asserts the world is populated (room/mob counts, a
  leader present per tribe, recall reachable) — proving end-to-end runnability.
- **Load-harness sketch (for the M14 latency criterion).** A scripted set of N
  synthetic sessions (Evennia's session/portal test utilities or a telnet load
  script) that connect, move, attack, and cast, while a timer records per-command
  server-side latency. M15 ships the *populated, bootable target* and this sketch;
  the actual 50-player <100 ms **measurement** is the M14 task that consumes it.
  The harness must report, not silently cap, the population it actually drove.

These three (boot hook, headless population check, load sketch) are what convert
"the systems are green in unit tests" into "the game runs," which is the
precondition every deferred M14 item named.

---

## 12. Cross-references

- Zone data shapes + the idempotent room/exit/NPC builder: zones spec (`zones.md`).
- Spawn-point derivation + leadership halt + scouting + Shrine cycle: repop spec
  (`repop.md`); owner is `repop_manager`.
- Season reset ordering + persistence boundary: seasonal-reset spec.
- Quest deed/giver/evidence model and the M13 review fixes (F1 giver-key, F3 deed
  flags, F4 altar-only `end_season`): quests spec (`quests.md`) + `tasks.md` M13.
- Disguised-priest spy NPC, pool tagging, exposure-to-boss relocation: disguised-
  priest spec; owner is `priest_manager`.
- AC convention, dice/RNG seam, day/night clock: architecture §5.

---

## 13. Testable contract (→ `tests/world_build/`)

1. `world.build.templates.all_templates()` aggregates every zone's `MOB_TEMPLATES`
   with no duplicate key; `get_template` raises `KeyError` on an unknown key.
2. `spawn_mob` on a valid `SpawnPoint` produces a live `Mob` in the named room
   with `ac`, `hp`, `level`, `morale`, `faction_id`, `is_leader`, and `spawn_id`
   set from the record; the HP roll is deterministic under a seeded RNG.
3. `spawn_mob` returns `None` (and does not raise) when the target room is not
   built — the deferred-room safety property.
4. **Idempotency:** running `build_all()` twice yields exactly one live instance
   per spawn point (no duplicate mobs); the room/exit/NPC set is unchanged
   (extends the zones-spec idempotency test to mobs).
5. After `build_all()`, every cave tribe has its `chief` and `shaman` instances
   live, and killing both fires the existing leadership halt → scout spawn →
   faction tension path with **real** scout instances (ties M6 ↔ M15).
6. A respawn tick (`repop_manager.at_repeat`) re-instantiates a killed mob via the
   spawner (not a no-op); a retreating scout is despawned.
7. **Giver-key (F1):** an NPC/mob built with `giver_key` resolves through
   `commands.quests._giver_here`; the Hermit, Provisioner, and a tribe chief are
   reachable for `quest`/`accept`/`turnin`; a chief is unavailable as a giver while
   dead/halted and available again after respawn.
8. **Deed hooks (F3):** the relevant world event sets `deed_done` for a character
   with the deed quest accepted and is a no-op for one without it; the
   shrine-destroyed hook sets the flag **without** re-firing `end_season`
   (the altar remains the sole `end_season` trigger).
9. **Season rebuild:** `rebuild_world()` despawns stale instances and re-populates
   from the registry; player-persisted state (XP/gear/bank) is untouched.
10. **Boot/runnability:** booting the test server and running `build_all()` yields
    a populated world (positive room and mob counts, recall reachable, a leader per
    tribe) — the end-to-end "the game runs" assertion.

Each pure-data behavior (1) runs Django-free; the rest use the Evennia test
harness (architecture §6). The `tests/world_build/` suite is organized as
`test_templates.py` (pure), `test_spawner.py`, `test_orchestrator.py`,
`test_givers.py`, and `test_deed_hooks.py`.

---

## 14. Build slices (post-review)

After the M15 spec-review gate, the implementation is broken into loop-grabbable
slices, spec→test→impl each, in dependency order:

1. `templates.py` registry + `tests/world_build/test_templates.py` (pure).
2. `spawner.py` (`spawn_mob`/`spawn_scout`/`despawn`) + instance-identity
   idempotency; rewire `repop_manager._instantiate*`; `test_spawner.py`.
3. `orchestrator.build_all()` + `at_initial_setup` hook + initial population pass;
   `test_orchestrator.py` (incl. idempotency + leadership-halt integration).
4. Giver-key (F1): `records.py` field, builder + spawner write-through,
   `_giver_here` resolution; `test_givers.py`.
5. Deed hooks (F3): `events.py` + the in-world triggers; `test_deed_hooks.py`.
6. Season rebuild delegation + the boot/load-harness check; unblocks the M14
   measurement tasks.

---

## 15. Open decisions

None blocking. Two implementation choices are deliberately deferred to the slice
that hits them (not escalations — they do not reopen a locked decision):

- The exact management surface for an idempotent rebuild on a live DB (`@batchcommand`
  vs. an admin `build` command) — decided in slice 3 against the installed Evennia
  version, documented in `docs/decisions/` per CLAUDE.md §3.
- The load-harness transport (Evennia session test utilities vs. an external
  telnet driver) — decided in slice 6 when the M14 latency measurement is taken.

If implementation uncovers a genuine contradiction with a locked decision or an
unspecified behavior, escalate via `docs/questions.md` rather than inventing a
requirement (PROMPT.md).
