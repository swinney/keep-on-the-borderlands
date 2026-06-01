# Economy Spec (R-econ) — currency, shops, banking, XP-on-secure

The money layer of the Keep: a single coin currency, the four Keep shops
(provisioner, armorer, weaponsmith, trader), the moneychanger's bank, starting
gold at character creation, and the **XP-on-secure** link that turns recovered
treasure into the campaign's primary XP source. Design doc; the resolved design
decisions this formalizes live in `docs/open-questions.md` §"Economy"; tests in
`tests/economy/`.

This spec is the testable contract for the M7 task *"Provisioner shop + economy
(starting gold, pricing, gold sinks); bank."* It does **not** reopen any locked
decision — it makes the already-resolved economy concrete and testable.

Rules source: OSE B/X equipment list and treasure-as-XP pacing. The pure money
math (price tables, starting-gold roll, buy/sell arithmetic) lives in
`world/rules/economy.py` (no Evennia import, unit-testable without booting the
server, per CLAUDE.md §3 and architecture §1). The live shop/bank behavior and
the commands live in the Evennia layer.

---

## 1. Currency model

- **One coin unit = 1 gold piece (gp).** v1 collapses OSE's `pp/gp/ep/sp/cp` to a
  single integer `gp` value for simplicity; sub-gold coinage and exchange are out
  of scope. Gems and jewelry carry an integer gp appraisal value and convert to
  coin when sold to the Trader.
- Carried money is the integer `character.db.coin` (gp). Banked money is the
  integer `character.db.bank_balance` (gp). Both already exist on the Character
  typeclass; this spec defines the operations on them. Neither may go negative.
- Coin is **lootable**: it travels into the corpse on death and is restored on
  loot (`docs/specs/death.md` §2). Bank balance is **never** in the corpse
  (death.md §3) — banking is the death-safe haven.

## 2. The price list (OSE equipment, in `world/rules/economy.py`)

A single price table `PRICE_LIST: dict[str, int]` maps an item key to its **list
buy price in gp**, drawn from the OSE SRD equipment list. This is the one tuning
file for item prices (CLAUDE.md §3: thresholds in one config). Representative
entries (the implementing task fills the full set it needs; these anchor the
ranges and back the tests):

| item key | list price (gp) | shop |
|---|---|---|
| `torch` | 1 | provisioner |
| `oil_flask` | 2 | provisioner |
| `rations_standard` | 5 | provisioner |
| `rope_50ft` | 1 | provisioner |
| `holy_water` | 25 | provisioner |
| `dagger` | 3 | weaponsmith |
| `sword` | 10 | weaponsmith |
| `leather_armor` | 20 | armorer |
| `chain_mail` | 40 | armorer |
| `plate_mail` | 60 | armorer |
| `shield` | 10 | armorer |

Prices are positive integers. The table is the sole source of truth; shops read
from it (a shop never hard-codes a price).

## 3. Shops

Four shops, each a static NPC vendor in its Keep room (`docs/specs/zones/keep.md`).
A vendor has a **stock list** (item keys it sells) and a **buy multiplier** (the
fraction of list value it pays when buying loot from a player).

| vendor | room | sells (stock) | buys at |
|---|---|---|---|
| Provisioner | `provisioner` | torches, oil, rope, rations, holy water, sundries | — (no buy) |
| Armorer | `armorer` | armor + shields | — |
| Weaponsmith | `weaponsmith` | OSE weapons | — |
| Trader | `trader` | general sundries | **50% of list**; gems at full appraised value |

### 3.1 Selling — `sell <item>` (Trader)

- The Trader buys loot at `floor(list_price × 0.5)` (the **50%** rule from
  open-questions.md). Gems/jewelry sell at their **full** appraised gp value (no
  haircut), since their value is already the "cash" form of treasure.
- Selling removes the item and credits `character.db.coin += payout`.
- An item with no known list price and no gem value cannot be sold (the Trader
  refuses); the command reports this and changes nothing.

### 3.2 Buying — `buy <item>` (any vendor)

- Buying an item the vendor stocks costs its full `PRICE_LIST` value. The purchase
  succeeds only if `character.db.coin >= price`; otherwise it is refused with a
  "you can't afford that" message and nothing changes (no negative coin).
- On success: `character.db.coin -= price` and the item is created in the buyer's
  inventory.
- A vendor refuses to sell an item not in its stock list ("I don't deal in that").

### 3.3 Listing — `list` (a.k.a. shop browse)

- `list` while in a shop room shows the vendor's stock with prices. Pure display;
  no state change. (Command surface only; not separately unit-tested beyond
  rendering the price table.)

## 4. Banking (moneychanger, `bank` room)

The bank exposes three operations via commands, all of which only function in the
`bank` room:

- `deposit <amount>` — move `amount` gp from `coin` to `bank_balance`. Requires
  `coin >= amount`. An optional **deposit fee** (config `BANK_DEPOSIT_FEE_PCT`,
  default `0`) is taken from the deposited amount as a gold-sink knob: the player
  loses `amount` coin and the balance rises by `amount − floor(amount × fee)`.
  With the default `0` fee, deposit is lossless.
- `withdraw <amount>` — move `amount` gp from `bank_balance` to `coin`. Requires
  `bank_balance >= amount`. No fee on withdrawal.
- `balance` — report carried `coin` and `bank_balance`. Pure display.

Invariants: neither `coin` nor `bank_balance` may go negative; a deposit/withdraw
that would exceed available funds is refused and changes nothing; the **total**
of `coin + bank_balance` is conserved across a deposit/withdraw except for any
explicit deposit fee removed as a sink.

Bank balance is **death-safe** (death.md §3) and **persists across seasonal
reset** (`docs/specs/seasonal-reset.md` §"persists").

## 5. Starting gold

- A new character rolls **`3d6 × 10` gp** (OSE; avg ~105) at creation, credited to
  `character.db.coin`, to be spent on starting gear at the provisioner
  (`docs/specs/combat.md` §7). The roll uses the seeded-RNG seam from
  `world/rules/dice.py` so it is deterministic under test.
- Function: `starting_gold(rng) -> int` in `world/rules/economy.py`, returning a
  value in the inclusive range `[30, 180]` (i.e. `3d6 × 10`).

## 6. XP-on-secure (treasure → XP)

The OSE treasure-as-XP link (open-questions.md §"treasure→XP"), adapted for a MUD:

- **1 gp of secured value = 1 XP.** Treasure grants its XP when **secured**, not on
  pickup. "Secured" means either (a) the coin is **deposited to the bank**, or (b)
  the coin is **carried alive into a Keep room** (any room in the `keep` zone).
- Each gp of value is credited **once**: a per-character running counter
  `character.db.secured_xp_credited` tracks the lifetime gp already converted to
  XP, so re-depositing or re-entering the Keep with the same coin does not
  double-grant. The amount granted on a securing event is
  `max(0, total_secured_value − secured_xp_credited)`, where `total_secured_value`
  is `bank_balance` plus coin secured in the Keep.
- The grant adds to the character's `xp` trait (which feeds level lookup in
  `world/rules/progression.py`). Kill XP is separate and additive (per combat
  spec); this spec governs only the treasure portion.
- Pure helper: `secure_xp(total_secured_value, already_credited) -> (grant,
  new_credited)` in `world/rules/economy.py`, so the accounting is unit-tested
  without Evennia. The Evennia layer wires the trigger (on deposit and on Keep
  entry) and applies the grant.

This is a deliberate divergence from tabletop pickup-timing; it makes extraction
and banking the real risk/reward loop. Tunable to on-pickup later if it proves
unfun (open-questions.md) — without changing the pure helper's contract.

## 7. Gold sinks (level-pacing knobs)

Because gold ≈ XP, every sink is also a pacing knob (open-questions.md §"Gold
sinks"). The sinks owned or touched by this subsystem:

- **Shop purchases** — consumables (torches/oil/rations) and armor/weapon upgrades
  (§3.2).
- **Optional bank deposit fee** — `BANK_DEPOSIT_FEE_PCT`, default `0` (§4).
- Sinks owned by other subsystems and only referenced here: henchmen hire fees +
  treasure share (R5), inn rest fees / chapel donations (M7 tavern/inn task), the
  ogre bribe and quest costs (R9). This spec does not implement those; it only
  guarantees the coin arithmetic they rely on (no negative balances, conservation)
  is centralized here.

All tunable values (`PRICE_LIST`, buy multipliers, starting-gold formula constant,
`BANK_DEPOSIT_FEE_PCT`) live in `world/rules/economy.py` so a single file balances
the economy.

## 8. Commands (Evennia layer)

| command | room scope | effect |
|---|---|---|
| `buy <item>` | any shop room | purchase from the room's vendor (§3.2) |
| `sell <item>` | `trader` | sell loot at 50% / gems at full (§3.1) |
| `list` | any shop room | show vendor stock + prices (§3.3) |
| `deposit <amount>` | `bank` | coin → bank, optional fee (§4) |
| `withdraw <amount>` | `bank` | bank → coin (§4) |
| `balance` | `bank` | show coin + bank balance (§4) |

Commands validate scope (right room/vendor), validate funds, and never leave a
balance negative or money created/destroyed except by an explicit fee or a
shop's buy/sell spread.

---

## 9. Testable behaviors (→ `tests/economy/`)

Pure-core tests (no Evennia boot, `tests/economy/test_economy_rules.py`):

1. `PRICE_LIST` values are all positive integers; the anchor items in §2 have the
   listed prices.
2. `starting_gold(seeded_rng)` returns a value in `[30, 180]` and is deterministic
   for a fixed seed (same seed → same value).
3. Trader buy payout is `floor(list_price × 0.5)` for priced loot; gems pay full
   appraised value.
4. `secure_xp` grants `total − already_credited` and never grants twice for the
   same gp: a second call with an unchanged total grants `0`; a call with a higher
   total grants only the delta; new credited equals the running total. It never
   returns a negative grant.
5. Buy arithmetic refuses when `coin < price` (returns unaffordable, no debit) and
   debits exactly `price` on success.
6. Deposit/withdraw arithmetic conserves `coin + bank_balance` (minus any fee),
   refuses overdrafts, and never produces a negative balance. With
   `BANK_DEPOSIT_FEE_PCT = 0`, deposit is lossless.

Engine/command tests (`tests/economy/test_economy_commands.py`, pytest-django):

7. `buy` in a shop creates the item, debits the price, and is refused (no change)
   when unaffordable or when the item is not in stock.
8. `sell` at the Trader removes the item and credits the 50% payout; refuses items
   with no sale value.
9. `deposit`/`withdraw` move coin between `coin` and `bank_balance`, only in the
   `bank` room, with the conservation/overdraft guarantees of behavior 6.
10. Securing coin (deposit, or entering a `keep`-zone room with carried coin)
    grants XP once per gp via the `secured_xp_credited` counter; re-securing the
    same coin grants no further XP.
11. Bank balance is unaffected by death (cross-check with `tests/death`): a
    character that dies and is looted keeps its full `bank_balance`.
