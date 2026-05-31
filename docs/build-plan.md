# Phased Build Plan (Deliverable #10)

The Ralph-Loop build order, smallest-shippable first, structured to maximize
**early integration** so architectural bugs surface before they compound
(CLAUDE.md §5). This is the input Phase 1 transforms into the root `tasks.md`.

Phase 0 already delivered, for every subsystem, a spec (`docs/specs/`), an
OpenSpec scenario set, and **skipped** test stubs (`tests/<system>/`). So each
milestone's loop work is mostly **unskip the stubs → implement until green**, not
write-tests-from-scratch. The spec → test → implement discipline (CLAUDE.md §3)
still holds: never weaken a spec or another system's tests to pass.

Per-milestone exit criterion is always: **the relevant `tests/<system>/` are
unskipped and green, and `ruff`/`mypy`/`pytest` all pass.**

---

## M0 — Bootstrap (Phase 1, human-run, pre-loop)

`evennia --init mudgame`; wire settings (tickers, gametime, contrib activation),
`at_initial_setup`; pin `evennia` in deps; add `pytest-django`; restore the mypy
Evennia/Django override and expand `[tool.mypy].files`; add `PROMPT.md`, empty
`STATUS.md`, generate root `tasks.md` from this plan. **Exit:** server boots, CI
green with the game dir present. (See `docs/specs/scaffolding.md` §6.)

## M1 — Rules core (smallest testable system)

`world/rules/`: `dice`, ability modifiers, ascending-AC math, attack/damage,
saves, HP, XP/level thresholds, morale — all pure, no Evennia. **Exit:** the
rules-level `tests/combat` scenarios green without booting Evennia.

## M2 — Combat on the engine

`Character`/`Mob` typeclasses, AC/HP wiring, ticker rounds + individual
initiative, attack/cast commands, a target dummy, minimal Vancian spells (light,
magic missile, cure light wounds, detect evil). **Exit:** a player fights a dummy;
0 HP triggers a death-handoff stub. `tests/combat` green.

## M3 — Death & hardcore

Corpse creation, XP-loss-to-level-start, recall revive at Inner Bailey, hardcore
deletion + leaderboard `fell` entry, who-list marker. **Exit:** `tests/death` green.

## M4 — Faction state machine

`world/factions/config.py`, `faction_manager`, standing/tension bands, event
deltas, decay, NPC aggression binding, `consider`. **Exit:** `tests/faction` green.

## M5 — Henchmen

Roster, hire (reaction roll), follow/orders, combat AI, loyalty/morale, XP +
treasure share, permadeath. **Exit:** `tests/henchmen` green.

## M6 — Repop + seasonal reset

Spawn-point registration, 15-min respawn, leadership halt, rival scouting, Shrine
24h cycle; `season_manager` orchestration of manager reset hooks, leaderboard
snapshot, `end_season`. **Exit:** `tests/repop` + `tests/seasonal_reset` green.

## M7 — Keep zone

Build `world/zones/keep/`: rooms, shops, bank, tavern roster, NPCs, recall,
chapel staff. Integrates henchmen hire, economy (starting gold, shops, banking),
and rest/memorization. **Exit:** a new character spawns, equips, hires, and rests.

## M8 — Wilderness zone

`world/zones/wilderness/` on `xyzgrid`: hex map, travel, wandering encounters,
set-pieces (hermit, spiders, lions, raiders). **Exit:** travel Keep → ravine mouth.

## M9 — Kobold cave vertical slice ⭐ (critical integration milestone)

ONE cave end-to-end: `world/zones/caves/` kobold lair, kobold mobs + chief/shaman
leaders, faction standing shifts, the leadership halt + rival scouting, a
Guildmaster tribe-clearing quest, and the treasure→XP-on-secure loop. This is the
milestone that surfaces every cross-system integration bug **before** seven more
caves are built the same way. **Exit:** an integration test runs the headline
acceptance loop — spawn → equip → hire a henchman → travel to the Caves → complete
a tribe-clearing quest → return and turn it in → bank for XP.

## M10 — Remaining caves

Orc Vile Rune + Decapitator (the playable war rivalry), goblins + ogre,
hobgoblins (King Nardo), bugbears, gnolls + owlbear, the minotaur maze + Shrine
passage. Reuses the M9 pattern. **Exit:** Caves complete; faction rivalries and
repop halts demonstrably fire under test.

## M11 — Shrine

`world/zones/shrine/`: temple rooms, the Adept boss, 24h reset, `no_recall` deep
rooms, the destructible altar wired to `end_season`. **Exit:** Shrine reset and
the season-end trigger tested.

## M12 — Disguised priest

`priest_manager`: rotation (no back-to-back repeat), clue assignment, the four
detection paths, the spy quest chain + ambush, exposure → Shrine boss, reset.
**Exit:** `tests/disguised_priest` green, including the two-season-rotation scenario.

## M13 — Quest catalog

Wire all 24 quests across givers, faction gates, repeatable/story state, and the
season-global effects (expose priest, destroy Shrine). **Exit:** `tests/quests` green.

## M14 — Polish & scale

Economy/XP-pacing balance pass; 50-player <100ms latency measurement (acceptance);
web-client theming + MOTD; encounter-table tuning. **Exit:** all acceptance
criteria in the OpenSpec prompt demonstrably met.

---

## Acceptance-criteria coverage map

| Acceptance criterion (prompt) | Milestone(s) |
|---|---|
| Spawn → equip → hire → travel → clear tribe → turn in | M7–M9 (proven at M9) |
| Faction transitions observable in NPC behavior | M4, M9 |
| Tribe repop halt + rival expansion fire under test | M6, M9 |
| Priest rotation differs across two simulated resets | M12 |
| Henchmen hire/follow/fight/share/refuse | M5 |
| Default death (XP+corpse) & hardcore (delete+leaderboard) | M3 |
| Season reset clears world, preserves characters | M6 |
| 50 players, <100ms command latency | M14 |

## Loop guidance

- Use a **verification subagent** on M4 (faction), M6 (reset), and M12 (priest) —
  the highest-bug-risk stateful systems (CLAUDE.md §5).
- One subsystem per commit; commit messages reference the milestone/task.
- If `docs/questions.md` starts growing, the specs are too thin — stop, expand,
  restart (CLAUDE.md §5).
