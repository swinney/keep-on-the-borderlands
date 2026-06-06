## Why

v1 acceptance (M0–M16, criteria C1–C8) delivered a built, populated, persistent
world with factions, repop, henchmen, economy, quests (effects wired), the
disguised-priest plot, death rules, seasonal reset, and the combat/spell engine.
But the acceptance gate never covered the **player-facing character layer**, and
two runtime seams were deferred. As a result the game today is an explorable world
with placeholder characters: `combat.md` §3/§6/§7 specify character creation,
leveling, and equipment that are **specced but unbuilt**, several quest-givers are
**unreachable**, and the load test runs **in-process** rather than over the wire.

This change captures all remaining gaps reported in the post-v1 audit so the loop
can build them. It is intentionally milestone-level (not hyper-granular): each
capability is a coherent, loop-able unit with a spec to derive tests from.

## What Changes

- **Character creation** (`combat.md` §7) — an in-game creation flow: roll `3d6×6`
  in order with one OSE-sanctioned swap; class/race selection gated by
  prime-requisite minimums (Cleric, Fighter, Magic-User, Thief; race-classes
  Dwarf, Elf, Halfling; no multiclass); derive L1 HP/AC/attack bonus/saves from the
  class+level tables; grant `3d6×10` starting gold; hardcore opt-in at creation.
  Today a new character is a generic blank (flat 10s, `char_class=None`).
- **Character progression** (`combat.md` §3/§6) — apply leveling in-game: when XP
  crosses a class threshold, advance level (1–10), roll new HP (`HD + CON mod`,
  min 1 via the existing `roll_hit_points`), and update attack bonus and saves from
  the class+level tables. The pure rules exist; the in-game advancement does not.
- **Equipment** (`combat.md` §3/§6) — wield/wear gear so it affects combat: worn
  armor + shield feed `AC = 10 + DEX_mod + armor + shield`; the equipped weapon's
  die drives melee damage (replacing the `1d6` placeholder). Likely via the
  Evennia `clothing` contrib (architecture §2). Today bought weapons/armor are
  inert.
- **Quest runtime** — make all quest-givers reachable and deeds completable:
  resolve givers by an explicit quest-giver key (not display `role`), so the
  Hermit, disguised Spy, Provisioner, and tribe-chief givers work; wire the
  deed-completion **world-event hooks** that set completion flags (altar-destroyed,
  rations-delivered, captive-escorted, spy-package drop) and their **carrier
  objects** (M17d); stamp the live spy's `giver_key` on relocation. (Effects are
  already wired/tested; this connects the triggers.) Also correct stale "24 quests"
  prose → 26.
- **Wire-level latency harness** (M17e / ADR-0005) — a true 50-socket telnet load
  harness measuring end-to-end latency over the wire, the fallback to M16's
  in-process p95 measurement.

## Capabilities

### New Capabilities
- `character-creation`: in-game new-character flow — ability generation, class/race
  selection with prime-requisite gating, derived L1 stats, starting gold, hardcore
  opt-in.
- `character-progression`: in-game leveling — XP-threshold advancement applying HP
  rolls and class+level attack/save updates, capped at level 10.
- `equipment`: wield/wear gear that affects AC (armor/shield) and melee damage
  (weapon die), replacing the combat placeholders.
- `quest-runtime`: reachable quest-givers (explicit giver keys) and deed-completion
  world-event hooks + carrier objects + live-spy giver-key stamping.
- `latency-harness`: a wire-level (50-socket telnet) end-to-end latency harness.

### Modified Capabilities
<!-- None. This wires/extends existing subsystems (combat, quests, load harness)
     via new player-facing flows; it does not change a previously-specified
     requirement's behavior. The underlying OSE rules (HP/XP/AC/saves) are unchanged. -->

## Impact

- **Code:** new commands and creation menu (`mudgame/commands/`, likely a
  `character_creator`-contrib cmdset); leveling application on the character
  typeclass + an XP-award/advancement seam; equipment via the `clothing` contrib
  (wield/wear commands, AC/damage reads in `world/rules/combat.py` consumers);
  quest-giver key on NPC typeclasses + `commands/quests._giver_here`; carrier-object
  typeclasses + world-event deed hooks; a wire-level harness under `world/build/`.
- **Specs/docs:** `combat.md` §3/§6/§7 move from specced to implemented; `quests.md`
  giver/deed sections; `docs/playing.md` "Current state & limits" shrinks as each
  lands; ADR-0005 latency note updated when the wire harness ships.
- **Contribs:** likely adopt `character_creator` and `clothing` (document in
  `docs/decisions/`).
- **Constraint (CLAUDE.md §3):** each capability needs its spec + test scaffold
  before implementation; locked decisions (classes, level 1–10, ascending AC,
  no multiclass, PvP off) are honored, not reopened.
