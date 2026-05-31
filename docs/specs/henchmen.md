# Henchmen Spec (R5)

Hireable AI followers that make solo play viable without forced grouping
(CLAUDE.md §2). Canon to B2 (the module suggests hiring men-at-arms). Design doc;
testable contract in
`openspec/changes/b2-mud-v1-design/specs/henchmen/spec.md`; tests in
`tests/henchmen/`.

Rules source: OSE retainer/loyalty/morale. Henchmen are `Henchman` typeclasses
(NPC subclass, architecture §1) controlled by a lightweight behavior loop.

---

## 1. Hiring and the roster

- Hire from a **roster at the Keep's tavern** — a set of available NPCs, each with
  `(name, class, level 1, hire_fee, base_morale)`. Roster size ~6; entries refill
  over real time and fully refresh at season start.
- Hiring resolves an **OSE reaction roll** `2d6 + CHA reaction mod`: a poor result
  refuses (the recruit walks); a good result accepts. Accepting deducts the
  `hire_fee` upfront and adds the henchman to the player's party.
- A player may not exceed their **retainer cap** (§3).

### Hire fees (proposed, gp; tunable in config)

| Recruit | Fee | Notes |
|---|---|---|
| Torchbearer / porter (level 0) | 10 | non-combatant, carries light & loot |
| Light footman (Fighter 1, leather+spear) | 40 | front-line filler |
| Bowman (Fighter 1, bow) | 60 | ranged |
| Acolyte (Cleric 1) | 100 | healing — scarce, pricey |
| Apprentice (Magic-User 1) | 120 | one spell, fragile |

Fees are an early **gold sink**; ongoing cost is the treasure share (§4), not a
wage, matching OSE economics.

---

## 2. Loyalty and morale

Each henchman has a **loyalty** score (OSE scale), seeded at hire from the
employer's CHA loyalty modifier plus the reaction result:

| Loyalty | Behavior |
|---|---|
| ≤ 3 | deserts at the next opportunity |
| 4–5 | grudging; refuses risky orders |
| 6–8 | reliable |
| 9–11 | loyal; morale bonus |
| 12+ | fanatic; will not flee |

**Morale checks** (`2d6`, OSE) use loyalty as the target and fire on the same
triggers as combat morale (R8): first party casualty, party ≤50% strength, and on
a suicidal order. Failure → flee or refuse (§5).

### Loyalty adjustments

| Event | Δ loyalty |
|---|---|
| Survives a victorious fight | +1 (cap by band) |
| Paid a fair treasure share (§4) | +1 |
| Healed when wounded | +1 |
| Denied/short-changed treasure share | −2 |
| Ordered into obvious suicide | −1 (and triggers a morale check) |
| A fellow henchman dies | −1 |
| Employer flees leaving henchman behind | −2 |

---

## 3. Per-character cap

The cap is the OSE **Charisma maximum-retainers** value (1 at CHA 3 → 7 at CHA
18). For a typical CHA 9–12 character the cap is **4** — this is the proposed
answer to the open question, grounded in OSE rather than invented. A hard server
ceiling of **7** applies regardless (the CHA-18 max), keeping 50-player encounters
bounded.

---

## 4. XP and treasure share

- **XP:** each henchman that participated in a kill earns a **half share**; the
  party's XP is split among full shares (players) and half shares (henchmen), so
  hiring help genuinely slows the employer's leveling — the intended tradeoff.
- **Treasure:** a henchman demands a negotiated **treasure share** (default = half
  of a full party share, set at hire, adjustable). The player distributes loot via
  a `give-share` step; paying fairly raises loyalty, shorting it drops loyalty and
  can trigger desertion.
- Shares are computed in `world/rules/` (pure, testable) and applied by the
  henchman manager on kill/loot events.

---

## 5. Combat AI and orders

Behavior loop each combat round (after the employer, on the henchman's own
initiative): attack the employer's current target by default, or follow standing
orders. Recognized orders (commands in `commands/henchmen.py`):

| Order | Effect |
|---|---|
| `follow` (default) | moves with the employer between rooms |
| `attack <target>` | engages the named target |
| `guard <who>` | intercepts attackers on the guarded character |
| `wait` | holds position, defends self only |
| `retreat` | disengages and flees toward the recall point |
| `dismiss` | releases the henchman (no refund) |

A henchman whose loyalty band forbids it **refuses** risky orders (and the refusal
itself nudges loyalty). On failed morale it flees regardless of orders.

---

## 6. Death and re-hire

- **Permadeath:** a henchman reduced to 0 HP is dead and gone; gear it carried
  drops to its corpse (recoverable like any corpse, R7). The party slot frees.
- Replacements must be **re-hired** from the roster; the dead henchman does not
  return. Henchman death also drops surviving henchmen's loyalty (§2).
- Henchmen do **not** persist across seasonal reset (they are world NPCs, not
  player characters); the roster refreshes at season start.

---

## 7. Testable behaviors (→ `tests/henchmen/`)

1. A successful reaction roll + paid fee adds the henchman; a failed roll does not.
2. Hiring is blocked once the player is at their CHA-derived cap (and at the hard 7).
3. A henchman with `follow` moves room-to-room with the employer.
4. In combat a henchman attacks the employer's target by default.
5. Kill XP awards henchmen a half share and reduces the employer's share accordingly.
6. Paying a fair treasure share raises loyalty; shorting it lowers loyalty.
7. A failed morale check (`2d6 > loyalty`) makes the henchman flee.
8. A low-loyalty henchman refuses a suicidal order.
9. Loyalty adjusts per the event table (heal +1, denied share −2, ally death −1, …).
10. A henchman at 0 HP is permanently removed and frees its party slot.
11. Roster refreshes at season start; henchmen do not persist across reset.
