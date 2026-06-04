M15 COMPLETE & MERGED (PR #22, merge commit 74b8153). ⏸ PAUSED before M16 per
operator instruction — do NOT start M16 / the M14 acceptance criteria without a
go-ahead.

M15 (world bring-up / runtime orchestrator) is on main: the game now actually
runs a populated world. `world/build/` boots every zone, spawns mobs/NPCs/leaders
from the registries (real spawning replaces the no-op `_instantiate`), resolves
quest-givers by explicit `giver_key`, fires world-event deed hooks, rebuilds the
world on season reset, and ships a headless boot + load-harness sketch. The M13
deferrals (F1 giver-key, F3 deed hooks, F4 altar-only end_season) are resolved.
776 tests passing, ruff + mypy --strict clean.

Built free-run by the Ralph loop (turns 67–79, Opus), spec-first with an operator
spec-review gate. Two issues were caught in review, not by the loop's own gate:
a full-suite regression (end_season's now-real rebuild broke the M11 shrine test
teardown — slice 6 had gated on subsets) and Copilot's F3 scout-death wiring gap
— both fixed before merge.

NEXT (do NOT auto-start — paused): M16 / the three now-unblocked M14 acceptance
criteria — economy/XP balance pass, 50-player <100ms latency measurement (the
load harness is ready), and full acceptance-criteria verification — plus the
remaining "Deferred follow-ups" in tasks.md (spell-disruption timing, Django-free
pure-test conftest, the spy giver-key stamping on the live season spy, the
delivery/escort/spy-drop deed triggers' carrier objects). The game is runnable, so
these are now doable.

Operating mode: loop-driven, walk-away — operator answers no questions, session
proceeds on its own recommendation (memory: loop-autonomy-mandate) — currently
overridden by the explicit "pause before M16" hold.
