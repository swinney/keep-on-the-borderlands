# Combat & Character Spec (R8)

OSE-faithful, round-based, ticker-driven combat plus the character creation and
class data it rests on. Design doc; testable contract in
`openspec/changes/b2-mud-v1-design/specs/combat/spec.md`; tests in `tests/combat/`.

Rules source: **Old School Essentials** SRD (open license) — reproduced as data
tables in `mudgame/world/rules/`. Locked conventions from `docs/architecture.md`
§5: **ascending AC**, dice through `world/rules/dice.py`, rounds on
`TICKER_HANDLER`.

---

## 1. Ability scores

Six scores: STR, INT, WIS, DEX, CON, CHA. Generated **3d6 in order** with one
allowed swap pair at creation (OSE-sanctioned, keeps low-roll characters viable
without point-buy). OSE modifier table:

| Score | 3 | 4–5 | 6–8 | 9–12 | 13–15 | 16–17 | 18 |
|---|---|---|---|---|---|---|---|
| Mod | −3 | −2 | −1 | 0 | +1 | +2 | +3 |

Score uses: STR → melee attack & damage, doors. DEX → AC, missile attack,
initiative. CON → HP per HD. INT → arcane languages (flavor v1). WIS → save vs
magic adj (flavor v1). CHA → henchmen cap & loyalty (R5), reaction.

---

## 2. Classes and race-as-classes

Per CLAUDE.md: Cleric, Fighter, Magic-User, Thief + race-as-class Dwarf, Elf,
Halfling. **No multiclass in v1.** Level range **1–10** (B2-scaled). Full XP,
attack-bonus, save, and spell-slot tables live in `world/rules/ose_tables.py` and
`world/rules/classes.py`; the SRD values are the source of truth and are not
re-typed here. Class shape:

| Class | Prime req | Hit die | Casts | Notes |
|---|---|---|---|---|
| Fighter | STR | d8 | — | best attack progression |
| Cleric | WIS | d6 | divine (from L2) | turn undead; no edged weapons |
| Magic-User | INT | d4 | arcane | weakest HD/armor; most spells |
| Thief | DEX | d4 | — | skills (climb, hide, move silently, pick locks, backstab) |
| Dwarf | STR | d8 | — | infravision; saves bonus vs magic |
| Elf | INT/STR | d6 | arcane | fighter + magic-user blend; detect secret doors |
| Halfling | DEX/STR | d6 | — | missile bonus; saves bonus; AC bonus vs large |

Class selection at creation is gated by OSE prime-requisite minimums; if no class
qualifies the player may re-roll. **Attack bonus** is the ascending value
(`attack_bonus = 20 − THAC0`), read from the table by class+level.

---

## 3. Derived stats

- **Hit points:** at each level roll the class hit die `+ CON mod`, minimum `1`
  gained per level. L1 may use max-HD house rule? No — OSE roll; `min 1`.
- **Armor class (ascending):** `AC = 10 + DEX_mod + worn_armor_bonus + shield`.
  Armor bonus comes from the `clothing`-contrib armor object (architecture §2).
- **Saving throws:** five OSE categories — Death/Poison, Wands,
  Paralysis/Petrify, Breath, Spells/Rods/Staves. Save succeeds when
  `d20 ≥ save_target(class, level, category)`.
- **Encumbrance:** simplified OSE — carried weight bands set movement; over
  capacity blocks travel. Coin weight counts (a gold sink pressure, see economy).

---

## 4. The combat round

Round-based, every combatant acts once per round. Real-time round length
**6 seconds** (tunable in settings), advanced by a per-fight `TICKER_HANDLER`
subscription. Sequence each round:

1. **Initiative** — individual: `1d6 + DEX_mod`, rerolled each round; higher acts
   first, ties resolved by higher DEX then coin flip. (OSE-sanctioned individual
   variant; chosen over group initiative for MUD responsiveness with mixed
   player/henchmen parties.)
2. **Declare & resolve** in initiative order: each actor takes one action —
   melee/missile attack, cast a memorized spell, flee, use item, or special.
3. **Morale checks** fire at trigger points (§6).
4. **Effects tick** — `buffs`-contrib durations decremented (architecture §2).

### 4.1 Attack resolution

`roll = 1d20 + attack_bonus + ability_mod + situational`

- `ability_mod` = STR for melee, DEX for missile.
- Hit when `roll ≥ target_AAC`.
- **Natural 20 always hits; natural 1 always misses** (adopted for clean,
  testable edge behavior).
- Damage = weapon die `+ STR_mod` (melee only), minimum `1`. Applied to target HP.

### 4.2 Death and dropping

A combatant at **0 HP is dead** (OSE default; no negative-HP bleed-out in v1).
Player death hands off to the death subsystem (R7): default XP loss + corpse, or
hardcore deletion. Mob death triggers XP award (split with henchmen, R5),
loot/corpse creation, and faction reputation deltas (R2).

---

## 5. Spellcasting (Vancian)

Arcane casters: Magic-User, Elf. Divine casters: Cleric (from level 2).

- **Memorization on rest:** a full rest (8 real-hours of in-fiction downtime, or
  at a safe location — exact gate in seasonal/economy tuning) lets a caster
  prepare spells into their per-level slots (count from the class table). Clerics
  pray for any spell on their list; Magic-Users/Elves prepare from their spellbook.
- **Casting** consumes one prepared slot of that spell. A spell can be prepared in
  multiple slots to cast it repeatedly.
- **Interruption:** taking damage in the same round before a spell resolves
  **disrupts** it — the slot is lost, no effect. (Casters declare on their
  initiative; a faster attacker can spoil the cast.)
- **Effects** are applied via the `buffs` contrib (durations) or immediate
  resolution (damage/heal/save-or-effect). Spell data in `world/rules/spells.py`.
- B2-relevant spells prioritized for v1: *light, magic missile, sleep, charm
  person, detect magic, hold portal* (arcane); *cure light wounds, detect evil,
  bless, light, protection from evil* (divine). **Detect Evil** is load-bearing
  for the disguised-priest detection path (R4).

---

## 6. Morale

Mobs and henchmen (not players) check morale on `2d6 ≤ morale_score`
(OSE; success = hold). Triggers: first casualty in the group, and when the group
drops to ≤ 50% strength. Failure → flee (mob) or refuse/flee (henchman, R5).
Morale scores are per-mob data in zone definitions; henchmen morale per R5.

---

## 7. Character creation flow

Via `character_creator` contrib + `EvMenu` (architecture §2):

1. Roll 3d6 × 6 in order; offer one swap.
2. Choose an eligible class (prime-req gated).
3. Roll HP (HD + CON mod, min 1).
4. Compute saves, attack bonus, AC base.
5. **Hardcore opt-in** — explicit, irrevocable confirmation (R7). Sets the
   permanent flag and who-list marker.
6. Starting gold **3d6 × 10 gp** (OSE); buy starting gear from the provisioner
   list (economy numbers in `docs/open-questions.md`).
7. Set name and `rpsystem` sdesc; spawn at the Inner Bailey recall point.

---

## 8. Testable behaviors (→ `tests/combat/`)

1. Ability modifier table maps every score 3–18 correctly.
2. AC = `10 + DEX_mod + armor + shield`.
3. Attack hits iff `d20 + bonus + mod ≥ AAC`; nat-20 always hits; nat-1 always misses.
4. Melee damage adds STR mod with a floor of 1; missile adds none.
5. Save succeeds iff `d20 ≥ target`; targets read from the class/level table.
6. HP per level = `max(1, HD_roll + CON_mod)`.
7. Individual initiative orders actors by `1d6 + DEX_mod`, rerolled per round.
8. A combatant reaching 0 HP is dead and hands off to the death subsystem.
9. Memorization fills slots per the class table; casting consumes a slot.
10. Taking damage before resolution disrupts a declared spell (slot lost).
11. Morale: group flees on a failed `2d6 ≤ morale` after a trigger.
12. Class selection is gated by prime-requisite minimums.
13. Hardcore opt-in sets the irrevocable flag during creation.
