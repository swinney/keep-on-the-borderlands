# Zones Spec (R1) — architecture & data model

Five zones, each its own Python package under `mudgame/world/zones/`, so the
Ralph Loop can build or revise one zone without touching another (CLAUDE.md §3).
This is the structural spec; the per-zone *content* lives in
`docs/specs/zones/{keep,wilderness,caves,shrine,unknown}.md`. Testable contract in
`openspec/changes/b2-mud-v1-design/specs/zones/spec.md`; tests in `tests/zones/`.

---

## 1. Zone package layout

Every zone is a package with a uniform shape (pure data + a thin build hook):

```
world/zones/<zone>/
├── __init__.py        # exposes build(<zone>) and metadata
├── rooms.py           # ROOMS: list of room records
├── exits.py           # EXITS: list of (from_key, direction, to_key) records
├── mobs.py            # MOB_TEMPLATES: faction-tagged stat blocks
├── spawns.py          # SPAWNS: room_key -> [mob_template, ...] + respawn (feeds R3)
├── npcs.py            # NPCS: static shop/quest NPCs + inventories
└── build.py           # build(): idempotent world-builder hook
```

Static content is **plain Python data structures** — no Evennia imports — so zone
data can be validated by tests without booting the server. Only `build.py`
imports Evennia, translating data into live objects.

### Record shapes (data, not behavior)

```python
Room   = {"key", "name", "desc", "zone", "coords"?,  # coords only for xyzgrid zones
          "dark"?, "no_recall"?, "details"?}          # details -> extended_room
Exit   = {"from", "dir", "to", "aliases"?, "locked"?, "key_item"?}
Mob    = {"key", "name", "faction", "level", "hd", "ac",  # ascending AC (arch §5.1)
          "attacks", "morale", "treasure", "is_leader"?, "leader_role"?}
Spawn  = {"room", "template", "count", "respawn_seconds", "is_leader"?}
Npc    = {"key", "name", "sdesc", "role", "inventory"?, "dialogue"?, "quests"?}
```

`faction` values are the exact ids from `docs/specs/faction.md` §1.1. `leader_role`
∈ {`chief`, `shaman`} feeds the R3 leadership-halt logic. Tribe membership for
repop is derived from `faction` on the spawn's template.

---

## 2. The world builder

A single builder (invoked from `server/conf/at_initial_setup.py` at first boot and
from the season-reset sequence, R6) calls each zone's `build()`:

- `build()` is **idempotent** — it creates rooms/exits keyed by a stable
  `zone:key` identity, updating rather than duplicating on re-run.
- It creates rooms, wires exits, registers spawn points with the `repop_manager`,
  and places static NPCs/shops.
- It does **not** spawn mobs directly; mobs come from the `repop_manager` reading
  the registered spawn points, so repop and initial population share one path.

The **Wilderness** zone uses the `xyzgrid` contrib (architecture §2): its rooms
carry `coords` and are built via the grid loader; all other zones use plain rooms.

---

## 3. The five zones (summary; detail in `docs/specs/zones/`)

| Zone | Package | Rough size | Role | Key systems |
|---|---|---|---|---|
| Keep | `keep/` | ~26 rooms | lawful hub: shops, bank, tavern, chapel, recall | henchmen roster (R5), disguised priest (R4), quest givers (R9), recall (Inner Bailey) |
| Wilderness | `wilderness/` | ~18 hexes | overland Keep→Caves with set-piece encounters | xyzgrid map, wandering encounters |
| Caves of Chaos | `caves/` | ~60 rooms | the humanoid lairs A–H | factions (R2), repop + leadership halt + scouting (R3), tribe quests (R9) |
| Shrine of Evil Chaos | `shrine/` | ~16 rooms | endgame temple | 24h reset (R3), exposed-priest boss (R4), season-ending quest (R6/R9) |
| Cave of the Unknown | `unknown/` | ~3 rooms (stub) | sealed teaser | reserved for a later release |

Total v1 world ≈ **120 rooms**, comfortably within a 50-player target.

---

## 4. Recall, travel, and connectivity

- **Recall point:** the Inner Bailey of the Keep (CLAUDE.md §2); flagged
  `no_recall` rooms (deep Shrine) block recall to preserve tension.
- Keep → Wilderness via the main gate; Wilderness → Caves via the ravine mouth;
  Caves → Shrine via a deep passage; Wilderness → Cave of the Unknown via a sealed
  entrance (stub).
- Dark caves are `dark` (require light — the torchbearer henchman, R5, and the
  *light* spell, R8, matter here).

---

## 5. Cave of the Unknown — disposition (open question resolved)

**v1 stub.** The module deliberately leaves this cave for the referee to design;
it has no canonical content. v1 ships a **sealed 3-room stub** (a collapsed/locked
entrance with flavor text and a "the way is barred — for now" hook), so:

- the architecture and exits exist (no dead pointer, no future migration), and
- no authoring budget is spent on non-canonical content competing with the Caves
  of Chaos, which is already the v1 content centerpiece.

A full mini-zone is deferred to a later release. Reasoning recorded in
`docs/open-questions.md`.

---

## 6. Testable behaviors (→ `tests/zones/`)

1. Every zone package exposes `build()` and the data lists (`ROOMS`, `EXITS`, …).
2. Every room `key` is unique within its zone; every exit `from`/`to` resolves to
   a real room (no dangling exits).
3. Every mob `faction` is a valid id from the faction config.
4. Every spawn `template` names a defined mob template; leader spawns carry a
   `leader_role` of `chief` or `shaman`.
5. Each tribe in the Caves has exactly one `chief` and one `shaman` spawn (R3
   leadership halt depends on this).
6. `build()` is idempotent — running it twice yields the same room/exit set.
7. The Inner Bailey exists and is the recall target; `no_recall` rooms reject recall.
8. Inter-zone exits connect the expected packages (Keep↔Wilderness↔Caves↔Shrine).
9. Ascending AC values on mob templates are in range (`≥ 10` base assumptions hold).
10. The Cave of the Unknown stub builds with a sealed entrance and no mobs.
