# Quest Catalog (R9)

24 quests spanning the B2 arc. Givers: Castellan, Curate, Guildmaster,
Provisioner, Hermit, tribe chiefs (faction-gated), and the rotating disguised
priest. Quest state is **per character**; some quests carry **season-global**
effects. Design doc; testable contract in
`openspec/changes/b2-mud-v1-design/specs/quests/spec.md`; tests in `tests/quests/`.

References zones (`docs/specs/zones/`), factions (`docs/specs/faction.md`), the
priest plot (`docs/specs/disguised-priest.md`), and seasonal reset
(`docs/specs/seasonal-reset.md`).

---

## 1. Quest record

```python
Quest = {
  "id", "giver", "title",
  "prereqs": [...],          # level, prior quest ids, faction standing gates
  "steps": [...],            # ordered objectives (kill/fetch/escort/report)
  "rewards": {"gp", "xp", "items"?, "standing"?},  # standing -> faction deltas (R2)
  "effects": {...},          # faction or season-global side effects
  "repeatable": bool,        # bounties repeat; story quests do not
}
```

State per character: `not_offered → available → active → complete` (+ `failed`).
`repeatable` bounties return to `available` after a cooldown; story quests stay
`complete`. Quest *completion history* persists across seasons (titles/lore);
*active progress* tied to world state resets (R6).

---

## 2. Guildmaster — combat bounties (repeatable)

| id | title | prereq | steps | reward | effects |
|---|---|---|---|---|---|
| `g_kobold_cull` | Cull the Kobolds | — | kill 8 kobolds | 50 gp, xp | `kobold` standing − |
| `g_orc_vile` | Break the Vile Rune | L2 | slay orc_vol chief | 150 gp, xp | R3 halt if shaman also dead |
| `g_orc_dec` | Break the Decapitators | L2 | slay orc_dec chief | 150 gp, xp | — |
| `g_bugbear_chief` | The Bugbear Grosh | L3 | slay bugbear chief | 200 gp, xp | — |
| `g_gnoll_chief` | The Gnoll Pack-Lord | L3 | slay gnoll chief | 200 gp, xp | — |
| `g_hobgoblin_king` | The Head of King Nardo | L4 | slay hobgoblin chief Nardo | 350 gp + weapon, xp | weakens cult's ally |
| `g_owlbear` | The Caged Horror | L3 | slay the owlbear | 175 gp, xp | — |
| `g_minotaur` | Into the Maze | L5 | slay the minotaur | 300 gp + map to Shrine | reveals Shrine passage |

## 3. Castellan — authority & story

| id | title | prereq | steps | reward | effects |
|---|---|---|---|---|---|
| `c_scout_caves` | Scout the Ravine | L1 | enter the Caves ravine, return | 40 gp, xp | unlocks bounties |
| `c_rescue_soldier` | The Captured Soldier | L2 | free the captive in orc_dec cave, escort home | 120 gp, xp | `keep` standing + |
| `c_expose_priest` | Treachery in the Chapel | evidence (R4) | report the spy with proof | title, 250 gp | **server-global exposed** (R4); spy → Shrine boss |
| `c_destroy_shrine` | Cleanse the Shrine | L7, `g_minotaur` | destroy the Altar of Chaos | 1000 gp + relic, xp | **`end_season`** (R6); server event |

## 4. Curate — chapel & detection

| id | title | prereq | steps | reward | effects |
|---|---|---|---|---|---|
| `cu_holy_water` | Vials of the Faithful | — | bring 3 empty vials; receive holy water | holy water ×3 | aids vs Shrine undead |
| `cu_suspicions` | The Curate's Doubt | ≥2 clue sightings (R4) | hear the Curate's suspicions | a clue + direction | advances priest investigation |
| `cu_bless_blades` | Consecrated Steel | L3 | donate 100 gp to the chapel | weapon blessed (vs cult) | gold sink |

## 5. Provisioner & Hermit

| id | title | giver | prereq | steps | reward | effects |
|---|---|---|---|---|---|---|
| `p_caravan` | The Stolen Caravan | Provisioner | L2 | recover goods from the bugbears | 130 gp, xp | `bugbear` standing − |
| `p_supplies` | Supplies for the Hermit | Provisioner | — | deliver rations to the hermit | 30 gp, xp | unlocks hermit |
| `h_rare_herb` | The Hermit's Errand | Hermit | `p_supplies` | fetch a "rare herb" (a trap) | hermit turns hostile; minor item | cautionary; no faction gain |
| `h_lions` | Trouble in the Hills | Hermit | befriended | clear the mountain-lion pack | 80 gp, xp | safer wilderness |

## 6. Tribe chiefs — play them against each other (faction-gated)

Available only at **non-hostile** standing with the giver tribe (R2). These shift
tribe-pair tension toward war (R2 `quest_aid_vs`).

| id | title | giver | prereq | steps | reward | effects |
|---|---|---|---|---|---|---|
| `t_vol_vs_dec` | Blood for the Vile Rune | orc_vol chief | standing ≥ neutral | kill 6 orc_dec | orc loot, xp | orc_vol↔orc_dec tension +8; `orc_vol` standing + |
| `t_dec_vs_vol` | The Decapitator's Due | orc_dec chief | standing ≥ neutral | kill 6 orc_vol | orc loot, xp | tension +8; `orc_dec` standing + |
| `t_gob_vs_gnoll` | Goblin Vengeance | goblin chief | standing ≥ neutral | kill the gnoll shaman | gem cache, xp | goblin↔gnoll tension +8 |
| `t_bribe_ogre` | Coin for the Ogre | goblin chief / player | gold | bribe the ogre to leave | the ogre departs (goblins weakened) | breaks goblin↔ogre alliance |

## 7. Disguised priest — the cult chain (R4, flagged `aids_cult`)

Offered by whichever NPC is the spy this season; appear benign.

| id | title | prereq | steps | reward | effects |
|---|---|---|---|---|---|
| `sp_package` | A Sealed Errand | talk to the spy | deliver a sealed package to a Caves drop | 60 gp | `aids_cult`; counts toward 3 |
| `sp_reagent` | Herbs for the Infirmary | `sp_package` | fetch a (poison) reagent from the swamp | 70 gp | `aids_cult`; counts toward 3 |
| `sp_minister` | Mercy for a Prisoner | `sp_reagent` | "minister" to a captured cultist in the cells | 80 gp | `aids_cult`; **3rd → Caves ambush + `cult` standing +** (R4) |

---

## 8. Cross-system effects summary

- **Season-global:** `c_expose_priest` (global exposed event), `c_destroy_shrine`
  (`end_season`). Both reset at season boundary (R6).
- **Faction (R2):** combat/aid quests apply `quest_aid`/`quest_harm` (±10 standing)
  and tribe quests apply `quest_aid_vs` (+8 pair tension).
- **Repop (R3):** chief-slaying bounties become leadership halts when the matching
  shaman is also dead.
- **Priest trap (R4):** the `sp_*` chain brands the player a cult collaborator on
  the third completion.

---

## 9. Testable behaviors (→ `tests/quests/`)

1. A quest progresses `available → active → complete` as its steps are met.
2. Prereqs gate availability (level, prior quest, faction standing).
3. Rewards grant the listed gp/xp/items on completion.
4. `quest_aid`/`quest_harm` apply the faction standing deltas (R2).
5. Tribe-chief quests are unavailable at hostile standing and apply `quest_aid_vs`.
6. The bribe-the-ogre quest breaks the goblin↔ogre alliance.
7. Completing the 3rd `aids_cult` quest triggers the Caves ambush and raises cult standing.
8. `c_expose_priest` requires valid evidence and fires the global exposed event.
9. `c_destroy_shrine` fires `end_season` and grants its reward.
10. Repeatable bounties return to `available` after cooldown; story quests stay complete.
11. Quest progress tied to world state resets at season boundary; completion history persists.
