# Zone Outline — The Caves of Chaos (`caves/`)

The heart of B2: a ravine of cave mouths, each a humanoid lair, mutually hostile
per the faction matrix (R2). ~64 rooms. This is where repop, leadership halts,
rival scouting (R3), faction shifts (R2), and tribe quests (R9) all play out.

Connectivity: `ravine` ↔ Wilderness `ravine_mouth`; a deep passage from the
`minotaur` maze ↔ Shrine (`shrine`).

**Adaptation note (recorded design choice):** the R3 leadership-halt mechanic
requires every tribe to have one `chief` and one `shaman` spawn. The module does
not give every tribe a shaman, so each tribe here is granted a shaman/witch-doctor
leader spawn for uniform, testable repop behavior. This is a deliberate deviation
from the printed module.

---

## The ravine (4 rooms)

| key | name | notes |
|---|---|---|
| `ravine` | The Ravine Floor | hub; all cave mouths open here; crossfire from sentries |
| `ravine_north` | North Ledges | mouths A, B, C |
| `ravine_mid` | Central Scree | mouths D, E |
| `ravine_south` | South Ledges | mouths F, G, H; passage deeper |

Each cave mouth is an exit from a ravine room into that tribe's lair.

---

## The lairs

Factions use the exact ids from `docs/specs/faction.md` §1.1. Each lair lists its
room count, leaders, roster, and treasure hook.

### Cave A — Kobolds (`kobold`, 6 rooms)
- Leaders: `chief` Sharptooth, `shaman` Grik.
- Roster: kobold sentries, warren of kobolds, guard dog pack.
- Treasure: modest coin; a captive (rescue quest hook, R9).
- Weakest tribe; bullied by orcs (rival = `orc_vol`, R3).

### Cave B — Orcs of the Vile Rune (`orc_vol`, 7 rooms)
- Leaders: `chief` Grukk, `shaman` Mawg.
- Roster: orc warriors, females/young (guarded chamber), war party.
- Treasure: chief's chest; a battle-standard (quest item).
- **At war with `orc_dec`** (the other orc tribe) — playable rivalry.

### Cave C — Orcs of the Decapitator (`orc_dec`, 7 rooms)
- Leaders: `chief` Bloodtusk, `shaman` Ssruk.
- Roster: orc warriors, ogre-skull totem guards.
- Treasure: a captured Keep soldier (rescue, R9); coin.
- **At war with `orc_vol`.**

### Cave D — Goblins + the Ogre (`goblin`, 8 rooms; ogre in 1 side cave)
- Leaders: `chief` Snagg, `shaman` Yeek.
- Roster: goblin warriors, wolves (mounts), the **Ogre** (`ogre`, allied — R2
  goblin↔ogre `allied`).
- Treasure: the ogre's hoard (bribe-the-ogre-away quest, R9).
- **At war with `gnoll`** (gnoll raids).

### Cave E — Hobgoblins (`hobgoblin`, 10 rooms — largest)
- Leaders: `chief` King Nardo, `shaman` Vurt.
- Roster: hobgoblin soldiers (disciplined), elite guard, females/young, a captive.
- Treasure: Nardo's strongbox (best tribe treasure); a magic weapon hook.
- Most organized; the Cult's intended first ally (R2 cult↔hobgoblin `peaceful`).

### Cave F — Bugbears (`bugbear`, 7 rooms)
- Leaders: `chief` Grosh, `shaman` Hrak.
- Roster: bugbear maulers (stealthy, surprise bonus), a captive merchant.
- Treasure: stolen caravan goods; coin.

### Cave G — Gnolls + the Owlbear (`gnoll`, 7 rooms; owlbear in 1 side cave)
- Leaders: `chief` Hrrl, `shaman` Mange.
- Roster: gnoll raiders, hyenas, the **Owlbear** (`owlbear`, beast, caged/feral).
- Treasure: raided loot; the owlbear's den has bones + a gem cache.
- **At war with `goblin`.**

### Cave H — The Minotaur's Maze (`minotaur`, 6 rooms)
- Solitary `minotaur` (no chief/shaman; not a repop tribe — beast rules).
- A small maze of twisty passages; the minotaur stalks intruders.
- Treasure: the minotaur's hoard at the maze heart; a passage onward.
- A deep exit from the maze leads to the **Shrine** zone.

---

## Systems wiring

- **Repop (R3):** every tribe's `chief` + `shaman` are leader spawns; killing both
  within one 15-min window halts that tribe 60 min and triggers the designated
  rival's scouting party into the empty lair (rival map in `docs/specs/repop.md`).
- **Factions (R2):** lair mobs carry their faction id; kills shift player standing
  and thaw/escalate tribe-pair tension per the matrix. The orc B↔C war and the
  goblin↔gnoll war are the showcase rivalries a party can exploit.
- **Quests (R9):** tribe-clearing bounties (Guildmaster), captive rescues
  (Castellan/Curate), the bribe-the-ogre quest, and cult-aiding spy quests (R4)
  that ambush the player here.
- **Light:** all lairs are `dark` — torches/`light` spell required (R8/R5).

Treasure values and gem/coin amounts: tuned with the economy numbers in
`docs/open-questions.md`.
