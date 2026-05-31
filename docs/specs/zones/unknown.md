# Zone Outline — The Cave of the Unknown (`unknown/`)

**v1 disposition: sealed stub** (open question resolved in `docs/specs/zones.md`
§5 and `docs/open-questions.md`). The module leaves this cave intentionally blank
for the referee to design; it has no canonical content. v1 ships a 3-room sealed
teaser so the architecture and the exit exist without spending authoring budget
on non-canonical content.

Connectivity: `cave_mouth` ↔ Wilderness `sealed_cleft`.

---

## Rooms (3)

| key | name | flags | notes |
|---|---|---|---|
| `cave_mouth` | The Cave Mouth | — | a dark opening in the cleft wall |
| `rubble_choke` | Collapsed Passage | `dark` | a cave-in bars the way deeper |
| `barred_door` | The Barred Door | `dark`,`no_recall` | an ancient sealed door; "the way is shut — for now" |

## Mobs / NPCs

None. The stub has **no spawns** (testable: `test_unknown_builds_as_sealed_stub`).

## Features

- The `barred_door` carries flavor text hinting at future content ("something
  waits beyond, but not this season").
- The package exists with the standard interface (`build()` + data lists) so a
  later release can flesh it into a full mini-zone with no migration — exits
  already point here from the Wilderness.
- No treasure, no quests, no faction presence in v1.

## Deferred (later release)

A full mini-zone (a small dungeon with one author's content, a unique mini-boss,
and a treasure reward scaled to mid-level parties) is the intended later
expansion. Tracked as out of scope for v1.
