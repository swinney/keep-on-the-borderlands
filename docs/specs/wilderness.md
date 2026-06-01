# Wilderness Zone Spec (M8)

Implementation spec for `mudgame/world/zones/wilderness/` — the overland map
between the Keep and the Caves of Chaos, built on the `xyzgrid` contrib.

**Zone content** (room names, encounters, set-pieces) is in
`docs/specs/zones/wilderness.md`. This document fixes the *structure*:
xyzgrid wiring, coordinate mapping, wandering-encounter mechanics, travel
commands, inter-zone exits, and testable behaviours.

---

## 1. Package layout

```
mudgame/world/zones/wilderness/
├── __init__.py       # exposes build(), MOB_TEMPLATES, SPAWNS, ENCOUNTER_TABLE
├── xymap.py          # XYMAP_DATA dict for the xyzgrid contrib
├── mobs.py           # MOB_TEMPLATES + ENCOUNTER_TABLE
├── spawns.py         # SPAWNS: leader/set-piece spawn points for the repop manager
├── npcs.py           # NPCS: the Mad Hermit (static NPC)
└── build.py          # build(): initialise xyzgrid + wire inter-zone exits
```

`rooms.py` and `exits.py` are **absent** — the xyzgrid contrib owns room and
exit creation for this zone. `xymap.py` replaces them as the single source of
truth for topology and room data.

Static content modules (`mobs.py`, `spawns.py`, `npcs.py`, `xymap.py`) carry
no Evennia imports, preserving the pure-data testability contract (zones spec
R1 §1).

---

## 2. xyzgrid coordinate mapping

The zone outline (`docs/specs/zones/wilderness.md`) uses logical "hex"
coordinates with y ∈ {−1, 0, 1, 2, 3}. The xyzgrid contrib requires non-
negative integer coordinates (origin at bottom-left). The implementation maps:

```
xyzgrid_y = outline_y + 1
```

So the 18 hexes land at:

| outline (x, y) | xyzgrid (x, y) | key              |
|---------------|---------------|-----------------|
| (0,  0)       | (0, 1)        | keep_road        |
| (1,  0)       | (1, 1)        | crossroads       |
| (1,  1)       | (1, 2)        | farmlands        |
| (2,  0)       | (2, 1)        | river_ford       |
| (2,  1)       | (2, 2)        | marsh_edge       |
| (2,  2)       | (2, 3)        | swamp            |
| (1,  2)       | (1, 3)        | woods_west       |
| (1,  3)       | (1, 4)        | woods_deep       |
| (3,  1)       | (3, 2)        | hermit_hut       |
| (3,  0)       | (3, 1)        | hills_low        |
| (3, -1)       | (3, 0)        | hills_high       |
| (4,  0)       | (4, 1)        | raider_camp      |
| (4,  1)       | (4, 2)        | old_tower        |
| (5,  0)       | (5, 1)        | ravine_approach  |
| (5,  1)       | (5, 2)        | ravine_mouth     |
| (4, -1)       | (4, 0)        | sealed_cleft     |
| (2, -1)       | (2, 0)        | glade            |
| (4,  2)       | (4, 3)        | overlook         |

The z-coordinate (map name) for the xyzgrid is the string `"wilderness"`.

---

## 3. Map string (MAPSTR)

The topology uses standard xyzgrid symbols: `#` nodes, `-` E-W links, `|` N-S
links. `sealed_cleft` uses the `I` (InterruptMapNode) symbol so auto-walk
always stops at the sealed entrance.

```
MAPSTR = r"""

+ 0 1 2 3 4 5

4   #
    |
3   #-#   #
    | |   |
2   #-#-#-#-#
    | | | | |
1 #-#-#-#-#-#
      | | |
0     #-#-I

+ 0 1 2 3 4 5

"""
```

Connectivity derived from this map:

| From          | To             | Dir  |
|--------------|---------------|------|
| keep_road     | crossroads     | e    |
| crossroads    | river_ford     | e    |
| river_ford    | hills_low      | e    |
| hills_low     | raider_camp    | e    |
| raider_camp   | ravine_approach| e    |
| ravine_approach | ravine_mouth | n    |
| crossroads    | farmlands      | n    |
| farmlands     | woods_west     | n    |
| woods_west    | woods_deep     | n    |
| farmlands     | marsh_edge     | e    |
| marsh_edge    | hermit_hut     | e    |
| hermit_hut    | old_tower      | e    |
| old_tower     | ravine_mouth   | e    |
| river_ford    | marsh_edge     | n    |
| marsh_edge    | swamp          | n    |
| woods_west    | swamp          | e    |
| hills_low     | hermit_hut     | n    |
| hills_low     | hills_high     | s    |
| raider_camp   | old_tower      | n    |
| raider_camp   | sealed_cleft   | s    |
| old_tower     | overlook       | n    |
| river_ford    | glade          | s    |
| glade         | hills_high     | e    |
| hills_high    | sealed_cleft   | e    |

All links are two-way (standard xyzgrid behaviour).

---

## 4. Room prototypes (xymap.py `PROTOTYPES`)

Each xyzgrid coordinate gets a prototype entry keyed by `(x, y)` (xyzgrid
coords), and `"room_key"` is stored as a custom attribute so the encounter
system can identify the hex without parsing coordinates.

```python
PROTOTYPES = {
    ('*', '*'): {
        "prototype_parent": "xyz_room",
        "key": "The Wilderness",
        "desc": "Open borderlands.",
        "attrs": [("zone", "wilderness")],
    },
    (0, 1): {
        "prototype_parent": "xyz_room",
        "key": "The Keep Road",
        "desc": "...",
        "attrs": [("zone", "wilderness"), ("room_key", "keep_road"), ("safe", True)],
    },
    # ... one entry per hex, with "room_key" matching the table above.
    # "safe": True on keep_road and glade only.
}
```

`safe = True` suppresses wandering encounters for that hex (see §6). Every
other non-default prototype omits `safe`, so it defaults to `False`.

Exit prototypes are left at the wildcard default (`('*', '*', '*')`).

---

## 5. Settings changes (M8)

Add to `mudgame/server/conf/settings.py`:

```python
EXTRA_LAUNCHER_COMMANDS = {
    "xyzgrid": "evennia.contrib.grid.xyzgrid.launchcmd.xyzcommand"
}
PROTOTYPE_MODULES += ["evennia.contrib.grid.xyzgrid.prototypes"]
```

These enable the `evennia xyzgrid` CLI and make `xyz_room`/`xyz_exit`
prototype parents available.

---

## 6. Build hook (build.py)

`build()` is called from `at_initial_setup` and from the season-reset sequence
(R6). It must be **idempotent** and must not import Evennia at module level.

```python
def build() -> None:
    from evennia.contrib.grid.xyzgrid.xyzgrid import get_xyzgrid
    from world.zones.wilderness.xymap import XYMAP_DATA

    grid = get_xyzgrid()
    grid.add_maps(XYMAP_DATA)
    grid.reload()
    grid.spawn(xyz=("*", "*", "wilderness"))
    _wire_interzone_exits()
```

`_wire_interzone_exits()` creates the non-grid exits that bridge the
wilderness to the Keep and the Caves (see §8). It is safe to call repeatedly
because it checks for existing exits before creating new ones.

---

## 7. Travel commands (CharacterCmdSet)

Add `evennia.contrib.grid.xyzgrid.commands.XYZGridCmdSet` to the
`CharacterCmdSet` in `mudgame/commands/default_cmdsets.py`. This activates:

- `map` — displays the current XYMap (builders only by default; relax to all
  players for the wilderness view).
- `goto <destination>` — auto-walk to a named room on the same xyzgrid map.
- `path <destination>` — show the shortest path without moving.

No custom travel command is needed; the xyzgrid commands handle all
grid-movement and pathfinding.

---

## 8. Inter-zone exits

The xyzgrid spawner deletes any cardinal-direction exit it did not create. All
exits bridging the wilderness to non-grid zones must therefore use
**non-cardinal keys** (with cardinal aliases for player convenience).

| From room key | Exit key | Aliases   | To (zone:room_key)      |
|--------------|----------|-----------|-------------------------|
| keep_road    | gate     | n, north  | keep:main_gate          |
| ravine_mouth | enter    | e, east   | caves:ravine_mouth      |
| sealed_cleft | cleft    | (none)    | unknown:entrance (stub) |

Conversely, `keep:main_gate` already has a south exit to `wilderness:keep_road`
(defined in the Keep zone exits). `caves:ravine_mouth` and `unknown:entrance`
will add their return exits when those zones are built (M9, stub).

`_wire_interzone_exits()` locates the target room via
`search_object_by_tag(zone:key, category=ROOM_CATEGORY)` and creates the exit
only if the target exists and the exit does not already exist. Deferred targets
(Caves not yet built at M8 time) are skipped silently, mirroring the
`build_exits` pattern in `world/zones/builder.py`.

---

## 9. Wandering encounter system

### 9.1 Trigger

On every movement into a wilderness room (detected via the room's
`at_object_receive(obj, source_location)` hook), if `obj` is a
`PlayerCharacter` and the room is not safe (`room.db.safe` is falsy), roll for
an encounter.

### 9.2 Roll

Roll `1d6`. On a **1**, an encounter occurs (≈17 % per move; tunable via
`WILDERNESS_ENCOUNTER_CHANCE` in `world/zones/wilderness/typeclasses.py` — the
1d6 threshold below which an encounter fires).

### 9.3 Encounter selection

Select one `MobRecord` at random from `ENCOUNTER_TABLE` — a list of
`(weight, mob_key)` pairs defined in `wilderness/mobs.py`. Weighted random
choice biases common wanderers (giant spiders, mountain lions, brigands) over
rare ones (cult undead, lizard raiders).

### 9.4 Spawn

Use `create_object` with the mob's typeclass (same as repop-spawned mobs) and
place it in the room. The spawned mob enters combat normally via its `at_object_receive`
hook. The encounter mob is **not** registered with the repop manager — it
despawns on death like any ordinary mob.

### 9.5 Safe hexes

`keep_road` and `glade` are marked `safe=True` in their prototypes. No
encounter roll is made in safe rooms.

---

## 10. Set-piece NPCs and spawns

The Mad Hermit at `hermit_hut` is a static NPC (placed by `build_npcs` after
the xyzgrid spawn). His pet mountain lion is a set-piece spawn registered with
the `repop_manager` via `SPAWNS` (respawn 15 min, not a leader).

All other wilderness set-piece mobs (giant spiders, brigands, mountain lions,
lizard raiders, cult undead) are in `SPAWNS` with zone-appropriate respawn
times. Leader mechanics do not apply in the wilderness (no tribe leadership
halt).

---

## 11. Testable behaviours (→ `tests/zones/test_wilderness.py`)

1. **Data integrity**
   - `xymap.XYMAP_DATA` contains `zcoord == "wilderness"`, a non-empty `map`,
     and a `prototypes` dict.
   - Every room key in `PROTOTYPES` appears in the coordinate table (§2).
   - `keep_road` and `glade` are the only entries with `safe=True`.

2. **Encounter table**
   - Every `mob_key` in `ENCOUNTER_TABLE` names a defined `MobRecord` in
     `MOB_TEMPLATES`.
   - All `MobRecord` factions are valid ids from the faction config.
   - Weights are positive integers.

3. **Spawns**
   - Every `SPAWNS` entry has a `template` naming a defined `MobRecord`.
   - No spawn carries a `leader_role` (wilderness has no leadership halt).

4. **Build (EvenniaTest)**
   - After `build()`, `XYZRoom.objects.filter_xyz(("*", "*", "wilderness"))`
     returns exactly 18 rooms.
   - `keep_road` room has `db.safe == True`; `crossroads` does not.
   - The `gate` exit exists on the `keep_road` room and points to the Keep's
     `main_gate` room (if the Keep was built first).

5. **Encounter mechanics (EvenniaTest)**
   - Moving a character into a non-safe room with a mocked roll of 1 spawns a
     mob in that room.
   - Moving a character into `keep_road` (safe) never spawns a mob regardless
     of roll.

6. **Map connectivity (pure-data)**
   - Parsing `MAPSTR` manually and extracting links verifies the connectivity
     table in §3 (all expected node pairs appear as linked).
