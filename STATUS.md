M12 COMPLETE — on branch m12-disguised-priest, paused at the M12→M13 gate for
review (PR open; Copilot review is the gate).

The disguised-priest plot is built (R4). Pure core in mudgame/world/priest/
(config, state, evidence, detection, quests, exposure — all Evennia-free and
mypy-strict), wrapped by the PriestManager GlobalScript which persists the
identity and wires the world reactions; the season_manager.reset_priest hook
calls reset_season at the season boundary. Slices, all spec→test→impl and green:
- seasonal identity rotation, never repeating the outgoing spy back-to-back;
- clue assignment from the pool (per-spy clue set);
- four detection paths (Detect Evil, Curate dialogue, witnessed nighttime act,
  planted object) over per-character Evidence (1 strong proof or 3 sightings);
- spy quest chain (3+ spy quests → Caves ambush, fired once at threshold);
- exposure → server-global event → spy unmasked, broadcast, flees to the Shrine
  boss_lair as a cult boss;
- season reset clears exposure, re-rolls identity, re-draws clues.
Live mob relocation (spy→boss) is a logged stub, consistent with the
project-wide no-op spawning (tests assert at registry/state level). 647 tests
passing, ruff + mypy --strict clean.

Built by a free-run Ralph loop (5 Opus turns, halted automatically at the
M12→M13 gate). One non-blocking anomaly: the clue-assignment turn committed then
over-ran its 1200s timeout (cost clock, not correctness).

Next: M13 — quest catalog (wire all 24 quests across givers; faction gating +
per-character story state; season-global effects). Build per docs/specs,
serially.
