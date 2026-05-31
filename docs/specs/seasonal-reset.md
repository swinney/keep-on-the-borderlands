# Seasonal Reset Spec (R6)

Each season is a campaign cycle: the world reacts to player action, then resets
so the reaction means something (CLAUDE.md §2 rejects both full persistence and
Diku total-repop). Design doc; testable contract in
`openspec/changes/b2-mud-v1-design/specs/seasonal-reset/spec.md`; tests in
`tests/seasonal_reset/`.

Owned by the `season_manager` GlobalScript, which **orchestrates** the other
managers' reset hooks rather than owning their logic.

---

## 1. Cadence (proposed answer to the open question)

**Default season length: 6 weeks (42 days), tunable in config.**

Reasoning:
- A focused player can take a character from level 1 to ~10 and experience the
  full B2 arc (Keep → wilderness → caves → Shrine, plus the priest plot) inside
  six weeks of casual play; a shorter season truncates the endgame, a longer one
  lets the political layer go stale.
- It gives the leaderboard a meaningful, repeatable competitive window and gives
  hardcore runs (R7) a deadline that matters.
- Six weeks ≈ a real-world "raid tier" rhythm players recognize, low enough
  operational overhead for a 20–50-player server.

Configurable so operators can run faster test seasons or longer live ones.

---

## 2. Persist vs reset

| Persists across reset | Resets at season boundary |
|---|---|
| Player characters (incl. hardcore flag) | Faction states & per-player standings (R2) |
| XP and level | Repop timers, halt windows, scouts (R3) |
| Gear and inventory | Disguised-priest identity, clues, exposure (R4) |
| Bank balance | Shrine state & boss (R3/R4) |
| Leaderboard (append-only) | Season-global quest effects (R9) |
| Quest *completion history* (for lore/titles) | Active quest *progress* tied to world state |
| — | Henchmen + tavern roster (R5; world NPCs, not PCs) |
| — | All live mob/room instances (rebuilt from zone data) |

The line is simple: **anything attached to a player Account/Character persists;
anything owned by a world manager or built from zone data resets.**

---

## 3. Reset procedure

The `season_manager` runs a deterministic sequence so the operation is testable
end to end:

1. **Warn** — broadcasts at T−24h and T−1h ("the season wanes…").
2. **Snapshot leaderboard** (§4) — capture final standings for the closing season.
3. **Flush world managers** by calling each one's documented reset hook:
   - `faction_manager` → clear standings, reseed tension from the matrix (R2).
   - `repop_manager` → clear timers/halts/scouts (R3).
   - `priest_manager` → re-roll identity + clue assignment, clear exposure (R4).
   - Shrine state → reset boss/rooms (R3).
4. **Reset season-global quest effects** (e.g. a destroyed Shrine is rebuilt; R9).
5. **Rebuild** live mob/room instances from `world/zones/` data; refresh the
   henchmen roster (R5).
6. **Advance** — increment `season_number`, set `season_start = now`.
7. **Broadcast** the new season with narrative framing ("A new season dawns over
   the Borderlands; the Caves stir with fresh menace.").

Player characters are never touched by steps 3–6.

---

## 4. Leaderboard (proposed scope: both)

**Maintain both a per-season board and an all-time board.** Reasoning: the
per-season board keeps competition fresh and winnable for newcomers each cycle;
the all-time board rewards legendary runs and gives long-term players something
permanent to chase. Cost is trivial (the per-season board is a filtered view of
the same append-only entries).

Entry fields: `character_name, class, level, season_number, hardcore (bool),
outcome, recorded_at`. `outcome` ∈ {`survived` (held at season end), `fell`
(hardcore death at level N, per R7)}.

- **Per-season board:** entries where `season_number == current`; the snapshot at
  reset freezes that season's top placements before the new season opens.
- **All-time board:** top hardcore final levels and top survivors across all
  seasons.
- Hardcore deaths (R7) append a `fell` entry immediately at death; survivors are
  recorded by the reset snapshot.

---

## 5. Early end

A season may end **before** the timer if a season-global quest fires the
`end_season` trigger — destroying the Shrine of Evil Chaos (R9) is the canonical
case. The `season_manager` exposes `end_season(reason)`, which runs the §3
procedure immediately with a bespoke broadcast ("The Shrine lies in ruins; the
season ends in triumph.").

---

## 6. Testable behaviors (→ `tests/seasonal_reset/`)

1. Reset invokes each world manager's reset hook (faction, repop, priest, Shrine).
2. Reset reseeds faction tension to the initial matrix and clears standings.
3. Reset preserves player level, XP, gear, and bank balance.
4. Reset increments `season_number` and sets a new `season_start`.
5. Reset takes a leaderboard snapshot before advancing.
6. Reset rebuilds mob/room instances and refreshes the henchmen roster.
7. Season-global quest effects (destroyed Shrine) are reverted on reset.
8. T−24h and T−1h warning broadcasts fire; a new-season broadcast fires after.
9. `end_season` runs the full procedure immediately and ends the season early.
10. The leaderboard exposes both per-season and all-time views; hardcore `fell`
    entries appear immediately, survivor entries at snapshot.
