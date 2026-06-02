M10 COMPLETE — paused at the M10 → M11 gate.

All Caves of Chaos built: kobold (M9) + goblin, hobgoblin, bugbear, orc
(Vile Rune + Decapitator), gnoll + owlbear, and the minotaur maze + Shrine
passage. The cross-tribe rivalry/repop-halt integration test is green
(576 tests passing, ruff + mypy --strict clean on main).

Built via the fan-out harness, which was then RETIRED as net-negative at this
scale (see docs/ralph-loop-experiment.md §3 (M10) + §5.13–5.16). M11 onward is
SERIAL — do not relaunch the fan-out.

Next: M11 — Shrine (world/zones/shrine/ temple rooms + no_recall deep rooms,
the Adept boss, 24h reset wired to M6, destructible altar -> end_season). Build
per docs/specs/zones/shrine.md, serially. (A rogue/unreviewed M11 shrine draft
exists in the ../kotb-wt/m10-orc clone as a reference only — build to spec, do
not salvage blindly.)
