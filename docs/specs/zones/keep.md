# Zone Outline — The Keep (`keep/`)

The lawful hub: recall point, shops, bank, tavern (henchmen roster), and the
chapel that hides the disguised priest. ~26 rooms, no hostile mobs. Faction id
for the garrison: `keep` (always friendly to lawful players, `war` with `cult`).

Connectivity out: the **Main Gate** opens onto the Wilderness (`wilderness`).

---

## Rooms (~26)

| key | name | notes |
|---|---|---|
| `main_gate` | Main Gate | entrance from the Wilderness; watched by crossbowmen |
| `gatehouse` | Gatehouse Passage | murder-holes; portcullis |
| `entry_yard` | Entry Yard | notices, bounty board (quest hooks) |
| `east_wall` | Eastern Wall Walk | view of the wilds |
| `west_wall` | Western Wall Walk | — |
| `outer_bailey` | Outer Bailey | central crossroads of the lower ward |
| `provisioner` | Provisioner's Store | gear, rations, light, oil (shop) |
| `armorer` | Armory | armor + shields (shop) |
| `weaponsmith` | Weaponsmith | weapons (shop) |
| `trader` | Trader's Post | general goods, buys loot (shop) |
| `bank` | Moneychanger & Vault | banking, deposits (gold sink, safe wealth) |
| `tavern` | The One-Eyed Cat | henchmen roster (R5), rumors, quest hooks |
| `inn` | The Traveller's Rest | rent a room to rest/re-memorize (R8) |
| `guild` | Guildhall | Guildmaster; combat/bounty quests (R9) |
| `chapel_nave` | Chapel Nave | Curate + chapel staff (disguised priest, R4) |
| `chapel_vestry` | Vestry | priest's cell; planted-object search (R4) |
| `chapel_bell` | Bell Tower | bellringer NPC; night-act vantage (R4) |
| `fountain_sq` | Fountain Square | gathering place |
| `smith_yard` | Smithy Yard | — |
| `stables` | Common Stables | mounts (flavor v1) |
| `warehouse` | Warehouse | crates; minor quest target |
| `bailiff` | Bailiff's House | watch quests |
| `inner_gate` | Inner Gatehouse | guarded; gates to the inner ward |
| `inner_bailey` | Inner Bailey | **RECALL POINT** (CLAUDE.md §2) |
| `audience` | Castellan's Audience Chamber | the Castellan; report priest here (R4) |
| `keep_tower` | Keep Tower | overlook; Corporal of the Watch |

## Exits / connectivity

`main_gate ↔ gatehouse ↔ entry_yard ↔ outer_bailey` spine; the Outer Bailey
fans out to all lower-ward shops, the tavern, inn, guild, and chapel;
`outer_bailey → inner_gate → inner_bailey` (recall) → `audience` and `keep_tower`.
Wall walks ring the outer bailey. `main_gate → wilderness:keep_road`.

## NPCs and inventory

| npc | room | role | inventory / function |
|---|---|---|---|
| Castellan | `audience` | lawful authority | receives priest report (R4); high-level quests |
| Curate | `chapel_nave` | chapel head | Detect-Evil hints; dialogue detection branch (R4) |
| Chapel staff ×5 | `chapel_*` | priest pool | `anselm/maeve/ortho/bellan/gisla`; one is the spy (R4) |
| Guildmaster | `guild` | quest giver | tribe-clearing & bounty quests (R9) |
| Provisioner | `provisioner` | shop | torches, oil, rope, rations, holy water, basic gear |
| Armorer | `armorer` | shop | leather→plate, shields (AC, R8) |
| Weaponsmith | `weaponsmith` | shop | OSE weapons |
| Trader | `trader` | shop | buys loot/gems; sells sundries |
| Banker | `bank` | service | deposit/withdraw; bank is death-safe (R7) |
| Tavernkeeper | `tavern` | service | henchmen roster (R5); rumor quests (R9) |
| Innkeeper | `inn` | service | rent room → rest/re-memorize |
| Corporal of the Watch | `keep_tower` | quest giver | wilderness patrol quests (R9) |

## Features

- **Spawn:** newly created characters spawn at `inner_bailey` (the recall point).
  Placed by `Account.at_post_create_character`, which resolves the `inner_bailey`
  recall tag *after* signup assigns the default `START_LOCATION` (Evennia → Limbo),
  since the project points no `START_LOCATION` at the Keep. (The character-level
  `at_object_creation` hook can't do this — the passed `location` overwrites it.)
- **Recall:** all recall returns to `inner_bailey`.
- **Rest:** the inn (or any safe Keep room) permits spell memorization (R8).
- **No combat** inside the Keep in v1 (PvP disabled; garrison repels intruders).
- Shop pricing and starting-gear costs: see `docs/open-questions.md` (economy).
