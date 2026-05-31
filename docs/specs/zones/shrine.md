# Zone Outline — The Shrine of Evil Chaos (`shrine/`)

The endgame temple beneath the Caves: home of the Cult of Evil Chaos (`cult`),
the Adept boss, and — once exposed (R4) — the disguised priest. ~16 rooms. Resets
wholesale every 24h with a server-wide broadcast (R3). Destroying it can end the
season early (R6/R9).

Connectivity: a deep passage from the Caves `minotaur` maze ↔ `shrine_gate`.
Deep rooms are `no_recall` to keep the climax committed.

---

## Rooms (~16)

| key | name | flags | notes |
|---|---|---|---|
| `shrine_gate` | The Black Gate | — | from the Caves; skull-carved doors |
| `narthex` | Defiled Narthex | — | cult sentries; warning bell |
| `nave_evil` | Nave of Chaos | `dark` | pews of bone; acolyte patrols |
| `side_chapel_n` | North Chapel | `dark` | offering of stolen Keep goods |
| `side_chapel_s` | South Chapel | `dark` | unholy font (holy-water counter) |
| `crypt_upper` | Upper Crypt | `dark` | skeletons/zombies (undead) |
| `crypt_lower` | Lower Crypt | `dark`,`no_recall` | wights; a sealed reliquary |
| `cells` | Prisoner Cells | `dark` | captives to free (quest, R9) |
| `acolyte_dorm` | Acolyte Dormitory | `dark` | cult acolytes rest here |
| `adept_study` | Adept's Study | `dark` | clues, the Shrine password, lore |
| `river_cavern` | Underground River | `dark`,`no_recall` | escape route; current hazard |
| `ritual_hall` | Hall of Ritual | `dark`,`no_recall` | set-piece ambush (priest chain, R4) |
| `inner_sanctum` | Inner Sanctum | `dark`,`no_recall` | the **Adept** boss; the altar |
| `altar_of_chaos` | Altar of Evil Chaos | `dark`,`no_recall` | destructible — season-end trigger (R9) |
| `boss_lair` | The Exposed One's Lair | `dark`,`no_recall` | exposed disguised priest boss (R4) |
| `secret_vault` | Secret Vault | `dark`,`no_recall` | best treasure; hidden door (Thief/Elf) |

## Mobs / factions (all `cult`)

| where | who | notes |
|---|---|---|
| `narthex`/`nave_evil` | cult sentries, acolytes | alarm raises the Shrine |
| `crypt_*` | skeletons, zombies, wights | undead; Clerics can turn (R8) |
| `acolyte_dorm` | adept acolytes (spellcasters) | hold/charm spells |
| `inner_sanctum` | **the Adept** (cult leader, boss) | the standing endgame boss |
| `boss_lair` | **the exposed priest** (boss) | present only after exposure (R4) |

The whole zone is faction `cult` (R2): `keep ↔ cult = war`; the priest plot can
shift tribe↔cult relations toward `allied` before exposure.

## Systems wiring

- **24h reset (R3):** all Shrine mobs/boss respawn, state clears, server-wide
  broadcast ("the cult regroups in the deep places").
- **Exposed priest (R4):** on global exposure the spy relocates to `boss_lair`
  as a `cult` boss until season end / Shrine reset restores it.
- **Season-end (R6/R9):** the `altar_of_chaos` is destructible; the
  Shrine-destruction quest fires `end_season` with a triumphant broadcast.
- **No recall** from `no_recall` rooms — once deep, players fight or flee on foot.
- **Light required** throughout (`dark`).
