# Disguised Priest Spec (R4)

The module's most interesting NPC: an evil priest hidden among the Keep's chapel
staff. Adapting a one-shot secret to a persistent, shared world is the hardest
narrative problem in B2. Design doc; testable contract in
`openspec/changes/b2-mud-v1-design/specs/disguised-priest/spec.md`; tests in
`tests/disguised_priest/`.

Owned by the `priest_manager` GlobalScript. Identity-hiding rides on the
`rpsystem` contrib (architecture §2): until a player identifies the spy they see
its `sdesc`, not its name.

---

## 1. The core problem and the solution

A server-global one-shot secret would mean **the first player to solve it wins
forever** and everyone after reads spoilers. CLAUDE.md rejects per-player
instancing (it breaks the shared world). The resolution:

- **Investigation is per-character.** Every player gathers clues and evidence on
  their own; nobody's discovery spoils anyone else's hunt.
- **Exposure is server-global, once.** When *any* player reports the spy to the
  Castellan with sufficient evidence, the world reacts a single time: the spy
  flees and becomes a Shrine boss everyone can then confront.
- **Identity rotates every season** and never repeats back-to-back, so the puzzle
  is fresh each cycle and can't be memorized.

---

## 2. Cast and assignment

A pool of **5 chapel NPCs** (one is the spy each season):

| id | sdesc | role |
|---|---|---|
| `anselm` | a soft-spoken friar | almoner |
| `maeve` | a stern sister | keeper of the reliquary |
| `ortho` | a portly deacon | leads daily services |
| `bellan` | a young bellringer | tends the chapel bell |
| `gisla` | a wandering pardoner | sells indulgences |

At each season start the `priest_manager`:

1. Picks `spy = random_choice(pool excluding last season's spy)` — **never the
   same NPC two seasons running**.
2. Draws a **clue set** of `CLUE_COUNT = 3` distinct clues from the clue pool and
   attaches the corresponding *tells* to the spy.
3. Clears all exposure state.

### Clue pool

`lights black candles at midnight`, `owns a black-handled dagger`, `knows the
Shrine's password`, `flinches from holy water`, `omits the Lawful litany at
prayer`, `meets a hooded visitor after dark`, `the chapel cat will not approach`.

Each clue maps to an in-world *tell* the spy exhibits (a nighttime act, a planted
object, a dialogue slip, etc.) — clues are not just lore text, they are the
observable hooks the detection paths key off.

---

## 3. Detection paths (per-character evidence)

Each path yields **evidence**; a player needs **one strong proof or three clue
sightings** to be able to report.

| Path | Mechanic | Yields |
|---|---|---|
| **Detect Evil** | a cleric of sufficient level casts Detect Evil (R8) on the spy | strong proof (evil aura) — innocents show nothing |
| **Curate dialogue** | the Curate shares suspicions once the player has logged ≥2 clue sightings | a clue + direction |
| **Witnessing a night act** | at game-night the spy performs a tell (e.g. lights black candles) in a chapel room; a present player observes it | a clue sighting |
| **Planted object** | searching the spy's cell/the chapel finds a clue object (black-handled dagger, password note) | a clue sighting (strong if the object is itself proof) |

Evidence is tracked **per character** on the Character (so investigation is
private). The `priest_manager` only holds the global identity/clue assignment and
the exposure flag.

---

## 4. The spy's quest chain

The spy, while unexposed, offers seemingly benign quests that **subtly aid the
Shrine** (deliver a sealed package to a Caves drop, "minister" to a captured
cultist, fetch an herb that is really a poison reagent). These are real entries
in the quest catalog (R9), flagged `aids_cult`.

- Completing **3 or more** spy quests triggers a **scripted ambush** in the Caves
  (cult forces fall on the player) and raises the player's `cult` standing (R2).
- Doing the spy's bidding is thus a trap that brands the player a cult collaborator
  — a deliberate alternate path through the plot.

---

## 5. Exposure flow

When a player with sufficient evidence **reports to the Castellan**:

1. Validate evidence; insufficient evidence is rejected with a warning ("you have
   suspicions, not proof").
2. Set the **server-global `exposed` flag**; broadcast ("Treachery in the chapel!
   <sdesc> is unmasked as a spy of Chaos and has fled!").
3. The spy NPC **leaves the chapel** and is (re)instantiated at the **Shrine as a
   boss** belonging to the `cult` faction (R3 Shrine zone).
4. The reporting player is credited (reward, lawful standing, possible title).
5. The chapel returns to a normal 5-NPC staff (the vacated slot filled by a plain
   acolyte) for the remainder of the season.

Once exposed, further investigation is moot — the secret is public — but the
**payoff is shared**: every player can now go fight the spy at the Shrine.

---

## 6. Reset behavior

At each season boundary (R6) the `priest_manager` reset hook:

- Re-rolls the spy (excluding the just-ended season's spy), redraws the clue set.
- Clears the `exposed` flag and all per-character evidence.
- Restores the spy NPC to the chapel and removes the Shrine boss instance.

---

## 7. Testable behaviors (→ `tests/disguised_priest/`)

1. At season start exactly one pool NPC is the spy.
2. The spy is never the same NPC as the immediately preceding season.
3. A clue set of `CLUE_COUNT` distinct clues is attached to the spy.
4. Two consecutive simulated resets yield different identities (and re-rolled clues).
5. Detect Evil on the spy yields strong proof; on an innocent NPC it yields nothing.
6. Witnessing the night act at game-night logs a clue sighting for the present player.
7. Searching finds the planted clue object and logs evidence.
8. The Curate branch unlocks only at ≥2 logged clue sightings.
9. Evidence is tracked per character (one player's progress does not appear on another's).
10. Completing 3+ spy quests triggers the Caves ambush and raises cult standing.
11. Reporting with sufficient evidence sets the global `exposed` flag, relocates the
    spy to the Shrine as a boss, and broadcasts.
12. Reporting with insufficient evidence is rejected.
13. Season reset re-rolls identity/clues, clears exposure and per-character evidence,
    and restores the chapel.
