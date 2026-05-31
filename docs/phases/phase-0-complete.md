# Phase 0 — Specification Generation: completion record

Moved here from `STATUS.md` during Phase 1 (M0) so that root `STATUS.md` can
serve its sole runtime role: the Ralph Loop's stop-signal mailbox (empty while
the loop runs; non-empty means "stop, here's why" — see `scripts/ralph.sh`).

Specification generation is finished. All 11 deliverables exist, are internally
consistent, and CI was green on `main` at completion.

## Deliverables

1. Architecture overview — `docs/architecture.md`
2. Subsystem specs (R1–R9) — `docs/specs/{zones,faction,repop,disguised-priest,
   henchmen,seasonal-reset,death,combat,quests}.md`
3. Test plan + skipped stubs — `tests/{faction,combat,repop,henchmen,
   seasonal_reset,disguised_priest,death,zones,quests}/`
4. Faction design — `docs/specs/faction.md`
5. Zone outlines — `docs/specs/zones/{keep,wilderness,caves,shrine,unknown}.md`
6. Quest catalog — `docs/specs/quests.md`
7. Henchmen design — `docs/specs/henchmen.md`
8. Seasonal reset — `docs/specs/seasonal-reset.md`
9. Disguised priest — `docs/specs/disguised-priest.md`
10. Build plan — `docs/build-plan.md`
11. Scaffolding plan — `docs/specs/scaffolding.md`

Plus: resolved open questions (`docs/open-questions.md`), escalation log
(`docs/questions.md`, no blockers), and the OpenSpec change `b2-mud-v1-design`
(proposal + 9 capability specs + design; `openspec validate` passes).

## OpenSpec change state

`proposal` done · `specs` done · `design` done · `tasks` deferred to Phase 1
and now realized as root `tasks.md` (generated from `docs/build-plan.md`).

## Resolved decisions (reasoning in `docs/open-questions.md`)

license=MIT, season=6wk, leaderboard=both, henchmen cap=CHA table, AC=ascending,
Cave-of-Unknown=v1 stub, economy=OSE treasure-as-XP with XP-on-secure, web
client=default+theming. One recorded module deviation: each Caves tribe is
granted a shaman spawn so the R3 leadership-halt mechanic is uniform.
