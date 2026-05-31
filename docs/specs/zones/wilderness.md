# Zone Outline — The Wilderness (`wilderness/`)

The overland route between the Keep and the Caves of Chaos, built on the
`xyzgrid` contrib (architecture §2) so rooms are coordinate hexes and the web
client can render a map. ~18 hexes with the module's set-piece encounters.

Connectivity: `keep_road` ↔ Keep main gate; `ravine_mouth` ↔ Caves;
`sealed_cleft` ↔ Cave of the Unknown (stub).

---

## Hexes (~18)

| key | coords | name | encounter / notes |
|---|---|---|---|
| `keep_road` | (0,0) | The Keep Road | gate to the Keep |
| `crossroads` | (1,0) | Crossroads | signpost; wandering-encounter node |
| `farmlands` | (1,1) | Abandoned Farmlands | low-level wandering mobs |
| `river_ford` | (2,0) | River Ford | crossing; ambush risk |
| `marsh_edge` | (2,1) | Marsh Edge | leads to the swamp |
| `swamp` | (2,2) | The Sunken Swamp | **lizard-folk** lair (faction `gnoll`? no — see below) |
| `woods_west` | (1,2) | West Woods | **giant spider** lair |
| `woods_deep` | (1,3) | Deep Woods | spider nest interior; webs slow movement |
| `hermit_hut` | (3,1) | The Mad Hermit's Hut | the **hermit** + pet **mountain lion** |
| `hills_low` | (3,0) | Low Hills | **mountain lions** territory |
| `hills_high` | (3,-1) | High Hills | raider lookout |
| `raider_camp` | (4,0) | Raider Camp | **bandits/brigands** ambush |
| `old_tower` | (4,1) | Ruined Tower | optional treasure; wandering undead at night |
| `ravine_approach` | (5,0) | Ravine Approach | the Caves loom |
| `ravine_mouth` | (5,1) | Ravine Mouth | gateway to `caves` |
| `sealed_cleft` | (4,-1) | Sealed Cleft | barred entrance to `unknown` (stub) |
| `glade` | (2,-1) | Quiet Glade | safe rest spot; rumor NPC |
| `overlook` | (4,2) | Borderlands Overlook | vista; map-reveal point |

## Set-piece encounters (NPCs / mobs)

| where | who | faction | notes |
|---|---|---|---|
| `hermit_hut` | the Mad Hermit + mountain lion | neutral→ambush | offers a misleading "quest"; turns hostile if pressed |
| `woods_west/deep` | giant spiders | beast (no pair politics) | poison save (R8); webbing |
| `swamp` | lizard raiders | tribe `lizard` (minor) | optional; or reskin as wandering bandits if `lizard` faction deferred |
| `hills_low` | mountain lions | beast | pack of 2–3 |
| `raider_camp` | brigands | `bandit` (minor) | human raiders; ransom/treasure |
| `old_tower` | skeletons (night only) | `cult` | tie-in: cult patrols at night |

Minor factions (`lizard`, `bandit`) default to `tense` with tribes per the
faction config's `DEFAULT_RELATION`; they exist mainly as wilderness threats and
are not part of the Caves leadership/repop politics.

## Features

- **Wandering encounters:** a light wilderness encounter table rolls on movement
  through non-safe hexes (data in `wilderness/mobs.py`); frequency tunable.
- **Travel gating:** the Caves are reachable only via `ravine_mouth`, so a new
  character must cross some wilderness — pacing the difficulty ramp.
- `glade` and `keep_road` are safe (no wandering encounters).
- Day/night matters (`extended_room`): the cult patrol and tower undead are
  night-only, foreshadowing the Shrine.
