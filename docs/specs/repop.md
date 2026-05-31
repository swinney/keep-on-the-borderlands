# Repop Spec (R3)

Tribe-scoped respawn that preserves the political layer (CLAUDE.md §2 rejects
Diku-style total repop for exactly this reason). Design doc; testable contract in
`openspec/changes/b2-mud-v1-design/specs/repop/spec.md`; tests in `tests/repop/`.

Owned by the `repop_manager` GlobalScript. Timers are **wall-clock** (real
minutes), not game time — see `docs/architecture.md` §5.2.

---

## 1. Concepts

- **Spawn point** — a static definition in zone data (`world/zones/<zone>/`):
  `(room, mob_template, respawn_seconds, is_leader, leader_role)`. The mob
  template names its faction (R2) and morale (R8).
- **Tribe** — the set of spawn points sharing a faction id. Has two designated
  leader spawn points: `chief` and `shaman`.
- **Halt window** — a per-tribe timestamp `repop_halted_until`; while in the
  future, *nothing* in that tribe repops.
- **Designated rival** — per-tribe config naming the tribe that moves in during a
  halt (the visible side of R2's "leadership broken" tension spike).

### Constants (config, tunable)

| Name | Value | Meaning |
|---|---|---|
| `STANDARD_RESPAWN` | 15 min | normal mob respawn delay |
| `LEADERSHIP_HALT` | 60 min | repop freeze after chief+shaman both dead |
| `SHRINE_RESET` | 24 h | Shrine of Evil Chaos full reset cycle |
| `SCOUT_PARTY_SIZE` | 3 | rival mobs sent into a broken lair |
| `MANAGER_TICK` | 60 s | how often the manager reconciles due spawns |

---

## 2. Standard respawn

On mob death the manager schedules `respawn_at = now + respawn_seconds` for that
spawn point (default `STANDARD_RESPAWN`). On each `MANAGER_TICK`, any spawn point
whose `respawn_at` has passed **and** whose tribe is not currently halted is
re-instantiated from its template at its room. Respawn is per-spawn-point, so
clearing a room buys ~15 minutes, not permanence.

---

## 3. Leadership halt

Leaders (`chief`, `shaman`) respawn on the **normal 15-min timer individually**.
A halt triggers only when **both leaders are dead at the same instant**:

- On any leader death, the manager checks whether the tribe's *other* leader is
  also currently dead. If so → set `repop_halted_until = now + LEADERSHIP_HALT`,
  emit a zone broadcast ("with chief and shaman both slain, the <tribe> warren
  falls into disarray"), apply R2 `leadership_broken` (+6 tension with each
  rival), and launch rival scouting (§4).
- **During the halt no tribe member repops** — including the leaders. After the
  window expires the *entire* tribe repops at the next tick with fresh leaders
  ("the <tribe> regroups").

Consequence: killing one leader is pointless on its own (it returns in 15 min);
the objective is to drop both within a single 15-minute window. That is the
testable tactical contract.

---

## 4. Rival scouting parties

While a tribe is halted, its now-empty lair is contested:

- The manager spawns `SCOUT_PARTY_SIZE` mobs of the **designated rival** faction
  into the broken tribe's lair rooms.
- Scouts belong to the rival faction for all R2 purposes — a player who fights
  them shifts standing with the *rival*, and their incursion is the in-world
  expression of the tension spike from §3.
- When the halt expires, surviving scouts **retreat** (despawn) as the original
  tribe regroups. If the player wipes the scouts too, the room simply stays empty
  until halt expiry.

Designated rivals (config):

| Broken tribe | Rival that moves in |
|---|---|
| kobold | orc_vol |
| orc_vol | orc_dec |
| orc_dec | orc_vol |
| goblin | gnoll |
| gnoll | goblin |
| hobgoblin | goblin |
| bugbear | hobgoblin |
| ogre / minotaur / owlbear | — (solitary, no scouting) |

---

## 5. Shrine reset

The Shrine of Evil Chaos (R1 `shrine` zone) is not tribe-scoped; it resets
wholesale every `SHRINE_RESET` (24 h):

- All Shrine mobs and the boss respawn; any in-progress Shrine state clears.
- A **server-wide broadcast** fires ("the cult regroups in the deep places").
- The disguised-priest boss (R4), if the priest was exposed and fled to the
  Shrine, is restored as part of the reset until the season ends.

---

## 6. Lifecycle

- Built at world build / season start: all spawn points instantiated, no halts.
- **Seasonal reset (R6):** clears all `respawn_at`, all halt windows, all scouts;
  re-instantiates from zone data. Player data untouched.
- The manager is the single owner of timers; typeclasses report deaths to it.

---

## 7. Testable behaviors (→ `tests/repop/`)

1. A killed standard mob respawns at its spawn point after `STANDARD_RESPAWN`.
2. Killing only the chief does not halt the tribe; the chief respawns in 15 min.
3. Killing chief and shaman while both are dead sets `repop_halted_until` to
   `now + LEADERSHIP_HALT` and fires the zone broadcast.
4. During a halt, no tribe member (including leaders) respawns.
5. A halt applies R2 `leadership_broken` (+6 tension with each rival).
6. Rival scouting spawns `SCOUT_PARTY_SIZE` rival-faction mobs into the lair.
7. Fighting scouts shifts standing with the rival faction, not the broken tribe.
8. On halt expiry the full tribe repops and surviving scouts retreat.
9. The Shrine resets every `SHRINE_RESET` with a server-wide broadcast.
10. Seasonal reset clears all timers, halts, and scouts.
