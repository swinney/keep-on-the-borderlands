# Faction System Spec (R2)

Scripted faction states: reactive enough to feel alive, bounded enough to test.
This is the design doc; the testable contract is
`openspec/changes/b2-mud-v1-design/specs/faction-system/spec.md`, and the test
plan is `tests/faction/`.

Locked by CLAUDE.md §2 "Faction System: Scripted States": per-tribe-pair state
∈ {allied, peaceful, tense, war}; per-(faction, player) standing ∈ {friendly,
neutral, hostile, kill-on-sight}; rule-based threshold transitions, not
simulation; all thresholds in one config file.

---

## 1. Concepts and data model

Two coupled relationships, each a discrete band derived from a hidden signed
integer. Driving the discrete states from integers makes every transition an
arithmetic delta against a threshold — trivially testable and tunable.

### 1.1 Factions

A **faction** is any group that can hold a relationship. v1 factions:

| id | display | type | can parley? |
|---|---|---|---|
| `kobold` | the kobolds | tribe | yes (if standing permits) |
| `orc_vol` | the orcs of the Vile Rune (Cave B) | tribe | yes |
| `orc_dec` | the orcs of the Decapitator (Cave C) | tribe | yes |
| `goblin` | the goblins | tribe | yes |
| `hobgoblin` | the hobgoblins | tribe | yes |
| `gnoll` | the gnolls | tribe | yes |
| `bugbear` | the bugbears | tribe | yes |
| `ogre` | the ogre | monster (mercenary) | yes (bribe) |
| `minotaur` | the minotaur | monster (solitary) | no |
| `owlbear` | the owlbear | beast | no |
| `cult` | the Cult of Evil Chaos | faction (Shrine) | no |
| `keep` | the Keep garrison | faction (lawful hub) | yes |

Beasts/solitary monsters (`minotaur`, `owlbear`) hold **player standing** but do
not participate in tribe-pair politics (they have no allies). `keep` is always
`friendly` to non-hardcore-criminal players and never a tribe-pair participant
beyond being `war` with `cult`.

### 1.2 Player standing — per `(faction, player)`

Hidden integer **reputation** `R`, starts at `0`. Discrete band by threshold:

| Band | Reputation range | NPC behavior |
|---|---|---|
| `friendly` | `R ≥ +15` | will not attack; offers parley/quests if `can parley` |
| `neutral` | `−14 … +14` | ignores player unless attacked |
| `hostile` | `−29 … −15` | attacks on sight if morale/numbers allow; may flee |
| `kill-on-sight` | `R ≤ −30` | always attacks, calls for help, refuses parley |

### 1.3 Tribe-pair relations — per unordered `{faction_a, faction_b}`

Hidden integer **tension** `T`, initialized from the module matrix (§3).
Stored once per unordered pair (symmetric). Discrete band by threshold:

| Band | Tension range | Inter-faction NPC behavior |
|---|---|---|
| `allied` | `T ≤ −10` | assist each other in combat; share aggro |
| `peaceful` | `−9 … +4` | coexist; ignore each other |
| `tense` | `+5 … +19` | wary; skirmish only if forced into the same room |
| `war` | `T ≥ +20` | attack each other on sight in shared rooms |

Band boundaries are **inclusive of the lower magnitude end** and defined once in
config so there is exactly one source of truth (`band_for(score, ladder)`).

---

## 2. Transition rules

All transitions are deltas applied by named events, then re-banded. No event
sets a band directly; bands are always recomputed from the integer. This keeps
"why did this change" answerable from an event log.

### 2.1 Player-standing events

| Event | Effect on `R(faction, player)` |
|---|---|
| Kill a member of `faction` | `−3` |
| Kill a `faction` chief or shaman | `−8` (leaders count extra) |
| Complete a quest that aids `faction` | `+10` |
| Complete a quest that harms `faction` | `−10` |
| Successful bribe/parley gift to `faction` (where allowed) | `+5` (capped at re-entering `neutral`; cannot buy `friendly`) |
| Player belongs to `cult`-aiding priest chain (3+ priest quests) | `cult` standing `+15`; all tribe standings unaffected |

Worked example (matches CLAUDE.md): from neutral `R=0`, five kobold kills →
`R=−15` → **hostile**; ten kills → `R=−30` → **kill-on-sight**. Leaders
accelerate it: chief+shaman+3 grunts = `−8−8−9 = −25` → hostile, nearly KOS.

### 2.2 Tribe-pair events ("the enemy of my enemy")

| Event | Effect |
|---|---|
| Player kills a member of `A` | for every rival `B` currently `tense` or `war` with `A`: `T(A,B) −= 1` (shared external threat thaws rivalries) |
| Player completes a quest aiding `A` against `B` | `T(A,B) += 8` (escalates toward war) |
| Player wipes `A`'s leadership (chief AND shaman — see R3) | `A` is "broken"; for each rival `B`: `T(A,B) += 6` (rivals move on the weakened tribe — feeds R3 rival scouting parties) |
| Disguised priest exposed and slain (R4) | every tribe-pair involving `cult` resets toward `war`; tribe-vs-tribe pairs unaffected |

Worked example (matches CLAUDE.md): kobold–goblin start `tense` at `T=+10`.
Killing kobolds repeatedly nudges `T` down `1` per kill; after 6 kills `T=+4` →
**peaceful**. The same kills also drive the player's `kobold` standing toward
hostile, so the thaw is paid for in kobold hostility — a real tradeoff.

### 2.3 Decay (anti-griefing, optional tuning knob)

Reputation and tension **drift toward their season-initial values** by `+1`/`−1`
per real 24h of no relevant events, never crossing the initial value. Default
`DECAY_ENABLED = True`. Decay never moves a value past `0` for standing or past
the configured initial for tension. This prevents permanent KOS from a single
bad day while preserving in-session consequence. Fully resets at season
boundary regardless (R6).

---

## 3. Initial tribe-pair matrix (mirrors B2 politics)

The module presents the Caves as a powder keg: tribes distrust one another, the
two orc tribes are blood enemies, the ogre is a hireling, and the Cult quietly
schemes to unite them. Initial tension values (band in parentheses):

|  | kob | o_vol | o_dec | gob | hob | gnoll | bug | ogre | cult |
|---|---|---|---|---|---|---|---|---|---|
| **kobold** | — | +12(t) | +12(t) | +10(t) | +8(t) | +14(t) | +14(t) | +2(p) | +6(t) |
| **orc_vol** |  | — | **+24(w)** | +10(t) | +8(t) | +12(t) | +10(t) | +2(p) | +6(t) |
| **orc_dec** |  |  | — | +10(t) | +8(t) | +12(t) | +10(t) | +2(p) | +6(t) |
| **goblin** |  |  |  | — | +12(t) | **+20(w)** | +14(t) | **−10(a)** | +6(t) |
| **hobgoblin** |  |  |  |  | — | +10(t) | +6(t) | +2(p) | +4(p) |
| **gnoll** |  |  |  |  |  | — | +10(t) | +2(p) | +6(t) |
| **bugbear** |  |  |  |  |  |  | — | +2(p) | +6(t) |
| **ogre** |  |  |  |  |  |  |  | — | +2(p) |
| **cult** |  |  |  |  |  |  |  |  | — |

Legend: a=allied, p=peaceful, t=tense, w=war. Module-grounded set-pieces:

- **orc_vol ↔ orc_dec = war (+24):** the two orc tribes are canonical enemies;
  a party can play them against each other.
- **goblin ↔ ogre = allied (−10):** the ogre lairs by the goblins and fights
  for them when paid (module text). Bribing the ogre away is a quest hook.
- **goblin ↔ gnoll = war (+20):** the gnolls raid the goblin warren.
- **cult ↔ everyone = tense (+6), softening with hobgoblins (+4):** the Cult is
  the most organized tribe and the Cult's first convert; the priest plot (R4)
  works to pull these toward `allied`.
- `minotaur`, `owlbear` omitted from the matrix — solitary, no pair politics.
- `keep ↔ cult = war`; `keep` holds no other tribe-pair entries.

---

## 4. Config schema (the single tuning file)

`mudgame/world/factions/config.py` — pure data, no Evennia imports, so its
correctness is unit-tested without booting the server.

```python
# Discrete bands, low→high magnitude, as (label, lower_bound_inclusive).
STANDING_LADDER = [
    ("kill-on-sight", None),   # R <= -30
    ("hostile",       -29),    # -29..-15
    ("neutral",       -14),    # -14..+14
    ("friendly",      +15),    # R >= +15
]
RELATION_LADDER = [
    ("allied",   None),        # T <= -10
    ("peaceful", -9),          # -9..+4
    ("tense",    +5),          # +5..+19
    ("war",      +20),         # T >= +20
]

STANDING_EVENTS = {
    "kill_member":  -3,
    "kill_leader":  -8,
    "quest_aid":   +10,
    "quest_harm":  -10,
    "bribe":        +5,   # capped at neutral
}
RELATION_EVENTS = {
    "kill_member_thaw":   -1,   # per rival in tense/war
    "quest_aid_vs":       +8,
    "leadership_broken":  +6,   # per rival
}

DECAY_ENABLED = True
DECAY_PER_DAY = 1

INITIAL_RELATIONS = {          # unordered pairs; see §3 matrix
    frozenset({"orc_vol", "orc_dec"}): +24,
    frozenset({"goblin", "ogre"}):     -10,
    frozenset({"goblin", "gnoll"}):    +20,
    # ... full matrix from §3 ...
}
DEFAULT_RELATION = +12         # any tribe pair not listed starts tense
```

Tuning is data-only: changing a number changes behavior with no code edit. A
test asserts every §3 matrix cell is represented and bands resolve as labelled.

---

## 5. NPC behavior binding

The manager exposes the bands; typeclasses read them at decision points.

- **On player entering a room** containing faction-F mobs: each mob checks
  `standing(F, player)`. `hostile`/`kill-on-sight` → initiate combat (subject to
  morale, R8/R5); `friendly` → may emit a parley/quest hook; `neutral` → idle.
- **On two factions sharing a room** (wilderness, rival scouting per R3): if
  `relation(A,B) == war` they engage; `allied` → they group; `tense` → posture,
  no attack unless one is already in combat; `peaceful` → ignore.
- **`consider <target>`** command surfaces the player's standing in flavor text
  ("the kobold sentry snarls — it would kill you on sight").

Aggregation when a room holds mixed factions: highest-threat standing wins for
the player; for inter-faction, the most hostile pair-band drives the room.

---

## 6. Lifecycle and ownership

- Owned by the `faction_manager` GlobalScript (`world/managers/faction_manager.py`).
- Per-player standing stored keyed by `(faction_id, player_dbref)`; per-pair
  tension keyed by the sorted faction-id tuple. All on the manager's Attributes
  (persisted via Django ORM, per architecture §4).
- **Seasonal reset (R6):** the manager flushes all standings and re-seeds tension
  from `INITIAL_RELATIONS`. Player data (XP/gear) is untouched.
- **Decay** runs on a low-frequency manager tick (hourly), applying §2.3.

---

## 7. Testable behaviors (→ `tests/faction/`)

1. `band_for` maps every boundary value to the correct label for both ladders.
2. Five `kill_member` events on `kobold` → standing `hostile`; ten → `kill-on-sight`.
3. `kill_leader` applies `−8` and re-bands correctly.
4. `quest_aid` / `quest_harm` move standing by `±10` and re-band.
5. Bribe cannot raise standing above `neutral`.
6. Killing `kobold` members lowers tension only with rivals currently `tense`/`war`.
7. kobold–goblin crosses `tense → peaceful` after the documented number of kills.
8. `quest_aid_vs` escalates a pair toward `war`.
9. `leadership_broken` raises tension with every rival (links to R3 scouting).
10. Initial relations match the §3 matrix; unlisted pairs default to `tense`.
11. Decay drifts values toward initial and never crosses it; disabled when
    `DECAY_ENABLED = False`.
12. Seasonal reset restores all factions to initial; player standing cleared.
13. NPC aggression reflects standing band (friendly no-attack; KOS always-attack).
