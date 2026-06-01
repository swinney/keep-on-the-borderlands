"""Pure economy core (R-econ / docs/specs/economy.md).

The single source of truth for money math: the OSE-derived price list, the
shop stock lists and Trader buy multiplier, the starting-gold roll, the
buy / deposit / withdraw arithmetic, and the XP-on-secure accounting. No
Evennia import — every function is value-in / value-out so the whole money
layer is unit-testable without booting the server (CLAUDE.md §3, architecture
§1). The live commands and the secure-XP trigger live in the Evennia layer
(``commands/economy.py``, ``world/economy``).

All tunable values live here so a single file balances the economy (spec §7).
"""

from __future__ import annotations

import math
import random

from world.rules.dice import roll

# ---------------------------------------------------------------------------
# §5 starting gold: 3d6 x 10 gp (OSE), via the seeded-RNG seam in dice.py.
# ---------------------------------------------------------------------------
STARTING_GOLD_NOTATION = "3d6"
STARTING_GOLD_MULTIPLIER = 10

# ---------------------------------------------------------------------------
# §3 buy/sell knobs and §4 bank fee (gold-sink). Default fee 0 → lossless.
# ---------------------------------------------------------------------------
TRADER_BUY_MULTIPLIER = 0.5
BANK_DEPOSIT_FEE_PCT = 0.0

# ---------------------------------------------------------------------------
# §2 price list — item key → list buy price in gp, drawn from the OSE SRD
# equipment list. The sole source of truth for prices; shops read from it and
# never hard-code a price. The §2 anchor items are exact; the rest fill out the
# stock the four Keep shops need.
# ---------------------------------------------------------------------------
PRICE_LIST: dict[str, int] = {
    # provisioner — sundries and consumables
    "torch": 1,
    "oil_flask": 2,
    "rope_50ft": 1,
    "rations_standard": 5,
    "rations_iron": 15,
    "holy_water": 25,
    "waterskin": 1,
    "backpack": 5,
    "sack_large": 2,
    "lantern": 10,
    "wolfsbane": 10,
    "garlic": 5,
    "mirror_steel": 5,
    "wooden_pole_10ft": 1,
    "iron_spikes_12": 1,
    "tinderbox": 3,
    # weaponsmith — OSE weapons
    "dagger": 3,
    "hand_axe": 4,
    "mace": 5,
    "war_hammer": 5,
    "short_sword": 7,
    "battle_axe": 7,
    "spear": 3,
    "sword": 10,
    "two_handed_sword": 15,
    "club": 3,
    "sling": 2,
    "short_bow": 25,
    "long_bow": 40,
    "crossbow": 30,
    "arrows_20": 5,
    "quarrels_30": 10,
    # armorer — armor and shields
    "leather_armor": 20,
    "chain_mail": 40,
    "plate_mail": 60,
    "shield": 10,
}

# ---------------------------------------------------------------------------
# §3 shop stock — vendor role → the item keys it sells. The Trader stocks a few
# general sundries and is the only vendor that *buys* loot (§3.1).
# ---------------------------------------------------------------------------
PROVISIONER_STOCK: tuple[str, ...] = (
    "torch",
    "oil_flask",
    "rope_50ft",
    "rations_standard",
    "rations_iron",
    "holy_water",
    "waterskin",
    "backpack",
    "sack_large",
    "lantern",
    "wolfsbane",
    "garlic",
    "mirror_steel",
    "wooden_pole_10ft",
    "iron_spikes_12",
    "tinderbox",
)
WEAPONSMITH_STOCK: tuple[str, ...] = (
    "dagger",
    "hand_axe",
    "mace",
    "war_hammer",
    "short_sword",
    "battle_axe",
    "spear",
    "sword",
    "two_handed_sword",
    "club",
    "sling",
    "short_bow",
    "long_bow",
    "crossbow",
    "arrows_20",
    "quarrels_30",
)
ARMORER_STOCK: tuple[str, ...] = (
    "leather_armor",
    "chain_mail",
    "plate_mail",
    "shield",
)
TRADER_STOCK: tuple[str, ...] = (
    "torch",
    "oil_flask",
    "rope_50ft",
    "rations_standard",
    "sack_large",
)

SHOP_STOCK: dict[str, tuple[str, ...]] = {
    "provisioner": PROVISIONER_STOCK,
    "weaponsmith": WEAPONSMITH_STOCK,
    "armorer": ARMORER_STOCK,
    "trader": TRADER_STOCK,
}

# Only the Trader buys loot (§3 table); every other vendor is sell-only to the
# player (i.e. the player buys from them).
BUYING_VENDORS: frozenset[str] = frozenset({"trader"})


def normalize_item_key(text: str) -> str:
    """Map free-text item input to a PRICE_LIST key: lowercase, spaces→underscores."""
    return "_".join(text.lower().split())


def starting_gold(rng: random.Random) -> int:
    """Roll a new character's starting gold: ``3d6 x 10`` gp (spec §5).

    Deterministic for a fixed-seed ``rng``; the result is always in [30, 180].
    """
    return roll(STARTING_GOLD_NOTATION, rng=rng) * STARTING_GOLD_MULTIPLIER


def trader_payout(*, list_price: int | None = None, gem_value: int | None = None) -> int | None:
    """Return what the Trader pays for an item, or None if it has no sale value (§3.1).

    Gems/jewelry sell at their full appraised gp value (``gem_value``); priced
    loot sells at ``floor(list_price x TRADER_BUY_MULTIPLIER)`` (the 50% rule).
    An item with neither a gem value nor a list price cannot be sold (None).
    """
    if gem_value is not None:
        return gem_value
    if list_price is not None:
        return math.floor(list_price * TRADER_BUY_MULTIPLIER)
    return None


def purchase(coin: int, price: int) -> tuple[bool, int]:
    """Resolve a buy (§3.2). Return ``(success, new_coin)``.

    Refused (``False``, coin unchanged) when ``coin < price``; otherwise the
    price is debited and the new coin total is returned (never negative).
    """
    if coin < price:
        return (False, coin)
    return (True, coin - price)


def deposit(
    coin: int,
    bank_balance: int,
    amount: int,
    *,
    fee_pct: float = BANK_DEPOSIT_FEE_PCT,
) -> tuple[bool, int, int]:
    """Resolve a bank deposit (§4). Return ``(success, new_coin, new_bank_balance)``.

    Refused (no change) when ``amount`` is non-positive or exceeds carried coin.
    On success the player loses ``amount`` coin and the balance rises by
    ``amount - floor(amount x fee_pct)`` — the fee is removed as a gold sink.
    With the default ``fee_pct`` of 0 the deposit is lossless.
    """
    if amount <= 0 or amount > coin:
        return (False, coin, bank_balance)
    fee = math.floor(amount * fee_pct)
    return (True, coin - amount, bank_balance + (amount - fee))


def withdraw(coin: int, bank_balance: int, amount: int) -> tuple[bool, int, int]:
    """Resolve a bank withdrawal (§4). Return ``(success, new_coin, new_bank_balance)``.

    Refused (no change) when ``amount`` is non-positive or exceeds the balance.
    No fee on withdrawal; ``coin + bank_balance`` is conserved on success.
    """
    if amount <= 0 or amount > bank_balance:
        return (False, coin, bank_balance)
    return (True, coin + amount, bank_balance - amount)


def secure_xp(total_secured_value: int, already_credited: int) -> tuple[int, int]:
    """XP-on-secure accounting (§6). Return ``(grant, new_credited)``.

    Each gp of secured value converts to 1 XP exactly once. The grant is
    ``max(0, total_secured_value - already_credited)`` — never negative — and the
    credited counter is monotonic (``max(already_credited, total_secured_value)``)
    so re-securing the same coin grants nothing.
    """
    grant = max(0, total_secured_value - already_credited)
    new_credited = max(already_credited, total_secured_value)
    return (grant, new_credited)
