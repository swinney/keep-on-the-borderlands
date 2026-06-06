Build order and gates follow the project loop pattern (CLAUDE.md §3: spec/test
before implementation; one milestone per review gate). Capabilities are largely
independent — this is the suggested order (design D6). Keep slices loop-able.

## 1. Character creation (capability: character-creation)

- [ ] 1.1 Spec/test scaffold: tests for `3d6`-in-order generation + one swap;
      prime-requisite gating per class; derived L1 HP/AC/attack/saves; starting
      gold `[30,180]`; hardcore opt-in irrevocable; spawn at Inner Bailey.
- [ ] 1.2 Spike + decide: `character_creator` contrib vs bespoke `EvMenu` (design
      D1/open-question); record the choice in `docs/decisions/`.
- [ ] 1.3 Implement the creation flow: ability roll + swap, prime-req-gated
      class/race selection (Cleric/Fighter/Magic-User/Thief + Dwarf/Elf/Halfling),
      derived L1 stats from the class tables, `3d6×10` gold, hardcore opt-in.
- [ ] 1.4 Keep direct (menu-less) creation working for tests/admin/headless boot.
- [ ] 1.5 Update `docs/playing.md` (creation section) and `combat.md §7` status.
- [ ] 1.6 ⛔ MILESTONE GATE — review, CI green, Copilot addressed; merge.

## 2. Character progression (capability: character-progression)

- [ ] 2.1 Spec/test scaffold: crossing a class XP threshold advances level (cap 10,
      multi-level jump resolves correctly, no de-level); level-up adds HP
      (`roll_hit_points`) and updates attack/saves from class+level tables;
      advancement is announced.
- [ ] 2.2 Verify the class+level attack-bonus and saving-throw tables exist for all
      seven classes, levels 1–10 (design risk); complete any gaps as spec-checked
      data.
- [ ] 2.3 Implement an `advance_if_ready` seam on the character; route every XP
      source (combat award, quest reward, secure-XP) through it.
- [ ] 2.4 Update `docs/playing.md` (leveling) and `combat.md §3/§6` status.
- [ ] 2.5 ⛔ MILESTONE GATE — review, CI green, Copilot addressed; merge.

## 3. Equipment (capability: equipment)

- [ ] 3.1 Spec/test scaffold: wield/wear/remove; `AC = 10 + DEX + armor + shield`
      (unarmored = `10 + DEX`); melee damage uses the equipped weapon die (unarmed
      fallback otherwise).
- [ ] 3.2 Spike + decide: `clothing` contrib vs custom equipment attrs (design D1);
      record in `docs/decisions/`.
- [ ] 3.3 Implement wield/wear commands + equipped state; give shop weapons/armor
      their damage die / AC bonus data.
- [ ] 3.4 Route AC through `computed_ac` and damage through the melee-damage feed so
      equipment changes one seam, not many.
- [ ] 3.5 Update `docs/playing.md` (combat note) — drop the placeholder caveat.
- [ ] 3.6 ⛔ MILESTONE GATE — review, CI green, Copilot addressed; merge.

## 4. Quest runtime (capability: quest-runtime)

- [ ] 4.1 Spec/test scaffold: giver resolution by explicit `giver_key` (Hermit,
      Spy, Provisioner, tribe-chief reachable); deed-completion hooks fire from
      world events; carrier objects invoke deed hooks; live-spy `giver_key` on
      assignment + relocation.
- [ ] 4.2 Add `db.giver_key` to giver NPCs (build/spawn time) and resolve on it in
      `commands/quests._giver_here`; define tribe-chief turn-in semantics.
- [ ] 4.3 Wire deed-completion triggers: `Altar.at_destruction` → shrine-destroyed;
      carrier objects for delivery/escort/spy-package → existing deed hooks.
- [ ] 4.4 Stamp the live spy's `giver_key` on seasonal assignment and on exposure
      relocation.
- [ ] 4.5 Fix stale "24 quests" → 26 in `docs/specs/quests.md` and
      `docs/build-plan.md`.
- [ ] 4.6 ⛔ MILESTONE GATE — review, CI green, Copilot addressed; merge.

## 5. Wire-level latency harness (capability: latency-harness)

- [ ] 5.1 Spec/test scaffold (integration tier, env-gated like the deployment
      smoke): 50 concurrent telnet clients, commands over the wire, p50/p95 report.
- [ ] 5.2 Implement the harness under `world/build/`; keep it out of the unit gate.
- [ ] 5.3 Update ADR-0005 and the acceptance spec to reflect wire-level measurement.
- [ ] 5.4 ⛔ MILESTONE GATE — review, CI green, Copilot addressed; merge.

## 6. Close-out

- [ ] 6.1 `docs/playing.md` "Current state & limits" reflects what now works; remove
      resolved limitations.
- [ ] 6.2 Confirm all five capability specs are satisfied; archive this change
      (`/opsx:archive`).
