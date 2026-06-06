## Context

The post-v1 audit found the OSE rules layer is built and tested
(`world/rules/`: `roll_hit_points`, `xp_for_level`/`level_for_xp`, `armor_class`,
saves, attack resolution, initiative) and the combat-round engine exists
(`CombatHandler` with initiative; spell declare/resolve/disrupt). What is missing
is the **player-facing wiring** that turns those rules into a playable RPG, plus
two deferred runtime seams. This change is the milestone-level capture; each
capability is built spec-first under the loop (CLAUDE.md §3).

## Goals / Non-Goals

**Goals:**
- A real character: create (roll/choose), level up, and equip gear that matters.
- Reachable quest-givers and firing deed-completion events.
- A wire-level latency measurement (ADR-0005 fallback).
- Reuse the existing pure rules; honor locked decisions (classes; level 1–10;
  ascending AC; no multiclass; PvP off).

**Non-Goals:**
- No new ruleset retuning, no new zones/content, no Cave of the Unknown.
- No new classes/races beyond the locked seven.
- Not GM tooling, not PvP.

## Decisions

### D1: Adopt Evennia contribs where they fit (architecture §2)
- **`character_creator`** for the creation flow (menu-driven chargen) rather than a
  bespoke menu, then layer the OSE rules (3d6-in-order + swap, prime-req gating,
  derived stats). *Alternative:* hand-built `EvMenu` — more control, more code;
  prefer the contrib and override only where OSE demands.
- **`clothing`** for equipment (wield/wear, equipped state) feeding AC/damage.
  *Alternative:* custom equipment attrs — rejected unless the contrib can't express
  weapon-vs-armor slots. Document the adopt/override choice in `docs/decisions/`.

### D2: Leveling triggers from the XP-award seam
Mob death already awards XP (combat.md §5). Advancement hangs off that award: after
XP changes, compare to `xp_for_level(class, level+1)` and, if crossed, advance
(loop for multi-level jumps), applying `roll_hit_points` and table-derived
attack/saves. Centralize in one `advance_if_ready`-style method on the character so
every XP source (combat, quest reward, secure-XP) converges on it.

### D3: Giver key separate from display role
Add an explicit `db.giver_key` to giver NPCs; `commands/quests._giver_here` resolves
on it (not `db.role`). Givers without a natural role match (Hermit, Spy,
Provisioner, tribe chiefs) get a giver key at build/spawn time. Tribe-chief turn-in
semantics defined explicitly (a chief may be both quest-giver and kill target).

### D4: Deed events fire from in-world triggers
Each deed-completion flag is set by the event that earns it: `Altar.at_destruction`
(already fires `end_season`) also sets shrine-destroyed; carrier objects
(delivery/escort/spy-package) call the existing deed hooks on reaching destination.
The completion *effects* are already wired/tested — this connects the *triggers*.

### D5: Wire harness mirrors the deployment-smoke tier
The 50-socket telnet harness needs a running server, so it is an opt-in
integration tier (env-gated, like the `RUN_DEPLOYMENT_SMOKE` smoke tests), not part
of the unit gate. It reports p50/p95 over the wire; ADR-0005 is updated when it
lands.

### D6: Build order (suggested milestones)
1. **character-creation** — unblocks having a real class to test the rest against.
2. **character-progression** — depends on a class being set.
3. **equipment** — independent of 1–2 but most meaningful with a real character.
4. **quest-runtime** — independent; reachable givers + deed events.
5. **latency-harness** — independent infra; do last or any time.
Each is its own milestone with a review gate.

## Risks / Trade-offs

- **Class+level attack/save tables may be incomplete.** §6 reads attack bonus and
  saves "from the table by class+level." → Verify the tables exist for all seven
  classes across levels 1–10; if partial, completing them is part of the
  progression milestone (data, spec-checked).
- **Contrib override surface.** `character_creator`/`clothing` bring their own
  cmdsets/typeclasses; integrating with `PlayerCharacter`, traits, and the recall
  spawn needs care. → Spike the contrib integration early in each milestone; keep
  OSE logic in `world/rules/` (pure), not in contrib glue.
- **Equipment touches combat consumers.** AC and damage are read in multiple
  places. → Route both through single sources (`computed_ac`, a `melee_damage`
  feed) so equipment changes one seam, not many.
- **Creation flow + non-interactive boot.** Chargen is interactive; ensure it does
  not break the headless/container path (the superuser/God char and tests must not
  require the menu). → Keep direct creation (no menu) working for tests/admin.
- **Quest-giver/kill-target overlap.** A tribe chief as both giver and target needs
  a defined interaction. → Decide in the quest-runtime spec/design slice.

## Migration Plan

Additive and incremental — each capability ships as its own merged milestone; the
game stays runnable throughout. `docs/playing.md` "Current state & limits" shrinks
as each lands. No data migration (new characters get the new flow; existing
characters are unaffected, though they predate rolled stats/classes).

## Open Questions

- `character_creator` contrib vs a small bespoke `EvMenu` — decide at the creation
  milestone's design slice after a quick spike.
- Do existing (pre-change) characters get a one-time "finish creation" path, or are
  they grandfathered as-is? (Default: grandfathered; new flow applies to new
  characters.)
- Equipment encumbrance — in scope now or later? (Default: later; this change does
  AC/damage effects, not encumbrance.)
