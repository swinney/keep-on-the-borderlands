# Death & Hardcore Spec (R7)

Two death models: a forgiving default (XP loss + corpse run) and an irrevocable
hardcore opt-in (permadeath + leaderboard). Design doc; testable contract in
`openspec/changes/b2-mud-v1-design/specs/death-and-hardcore/spec.md`; tests in
`tests/death/`.

Entry point: combat (R8) hands a 0-HP player to this subsystem. Recall point is
the **Inner Bailey of the Keep** (CLAUDE.md §2). Leaderboard mechanics live with
seasonal reset (R6); this spec writes the hardcore `fell` entry.

---

## 1. Death dispatch

On a player reaching 0 HP, the subsystem branches on the character's `hardcore`
flag (set irrevocably at creation, R8):

```
on_death(character):
    if character.hardcore:  -> hardcore_death(character)
    else:                   -> default_death(character)
```

Henchman death is **not** handled here — it is permadeath via R5.

---

## 2. Default death — XP loss + corpse run

1. **XP loss to start of current level.** Set `xp = xp_threshold(current_level)`.
   The character does **not** de-level; only in-level progress is lost. A death
   with zero in-level progress costs no XP (floor at the threshold).
2. **Corpse.** Create a `Corpse` object in the death room containing **all
   equipped items, all inventory, and all carried coin**. The corpse is a normal
   persistent object (architecture §4).
3. **Revive at recall.** Move the character to the Inner Bailey and restore it to
   `1` HP (enough to act, not enough to be safe). Memorized spells are cleared
   (must re-rest, R8).
4. **Corpse run.** The player returns to the death room and loots the corpse to
   recover gear and coin. **Bank balance is never in the corpse** — banked wealth
   is safe (a deliberate incentive to bank).
5. **Decay.** The corpse persists until looted or the season ends (configurable
   `CORPSE_TTL`, default = until season reset), so gear is not lost to a bad
   night. Anyone may loot a corpse — recovery is not access-controlled — adding
   stakes to a deep-caves death.

---

## 3. Hardcore death — permadeath + leaderboard

Hardcore is opt-in at creation and **irrevocable** (R8). On death:

1. **Drop a corpse** with the character's gear/coin in the death room (lootable by
   others — the gear stays in the world; only the character is gone).
2. **Append a leaderboard entry** `fell`: `{name, class, level (final), season,
   recorded_at}` (R6 leaderboard).
3. **Broadcast** a server-wide eulogy ("<name> the <class> has fallen at level N,
   season S").
4. **Delete the character.** The account may roll a new character; the fallen one
   does not return and has no corpse run for itself.

There is no XP-loss path for hardcore — death is terminal.

---

## 4. Hardcore visibility

- An irrevocable `hardcore` flag on the Character, set during creation.
- A **who-list marker** (e.g. a `[HC]` tag) and a title decoration so hardcore
  characters are recognizable in-world and on the who list (CLAUDE.md §2).
- The flag cannot be cleared by any command after creation.

---

## 5. Interactions

- **Seasonal reset (R6):** default corpses are cleared at reset (gear inside is
  lost if never retrieved — another reason to corpse-run promptly). Hardcore
  `fell` entries persist on the leaderboard.
- **Faction (R2):** dying does not itself change standings; the kills that led to
  death already applied their deltas.
- **Henchmen (R5):** if the employer dies, following henchmen check morale; the
  employer fleeing/dying can drop their loyalty.

---

## 6. Testable behaviors (→ `tests/death/`)

1. Default death sets XP to the current level's start threshold and does not de-level.
2. Default death with zero in-level progress leaves XP unchanged.
3. Default death creates a corpse in the death room holding all gear and carried coin.
4. Default death moves the character to the Inner Bailey at 1 HP and clears memorized spells.
5. Looting the corpse restores gear and coin to the player.
6. Bank balance is never placed in the corpse and is unaffected by death.
7. A default corpse persists until looted or season reset.
8. Hardcore death deletes the character.
9. Hardcore death appends a `fell` leaderboard entry with the final level and season.
10. Hardcore death drops a corpse lootable by other players.
11. The hardcore flag is set at creation and cannot be cleared afterward; the
    who-list marker is present.
