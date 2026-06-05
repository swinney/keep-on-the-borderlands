⏸ PAUSED at a clean point (operator requested context-clear). Nothing in
progress. main is green; no open work.

DONE: v1 acceptance-complete (M0–M16, PR #23) + post-v1 polish M17a (Django-free
conftests, #24), M17b (spell disruption declare/resolve/disrupt, #25), M17c
(installation & run guide + README destale, #26). The game is built, runnable,
acceptance-verified, and documented for an operator to install + run. 813 tests
passing, ruff + mypy --strict clean. 19 milestone gates passed; PRs #3–#26 all
reviewed (Copilot) and merged.

REMAINING (all OPTIONAL deferred polish — none gate v1; in tasks.md "Deferred
follow-ups"):
- M17d candidate: quest carrier-object deed triggers (delivery/escort/spy-package
  objects that call the existing, tested deed hooks) + live-spy `giver_key`
  stamping on relocation — completes the deed-quest loop end to end.
- M17e candidate: a true wire-level (50-socket telnet) latency harness — the
  ADR-0005 fallback to M16's in-process p95 measurement.

Operating mode: loop-driven, walk-away (memory: loop-autonomy-mandate). On the
next "continue": cut a branch per remaining item, loop→review→merge, same cadence.
