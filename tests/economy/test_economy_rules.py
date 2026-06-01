"""Pure-core economy tests (R-econ / docs/specs/economy.md §9 behaviors 1-6).

These exercise ``world.rules.economy`` with no Evennia boot: the price table,
the starting-gold roll, the Trader buy payout, the XP-on-secure accounting, and
the buy / deposit / withdraw arithmetic.
"""

from __future__ import annotations

import random

from world.rules.economy import (
    PRICE_LIST,
    deposit,
    purchase,
    secure_xp,
    starting_gold,
    trader_payout,
    withdraw,
)

# §2 anchor items and their exact list prices (the table is the source of truth).
_ANCHOR_PRICES = {
    "torch": 1,
    "oil_flask": 2,
    "rations_standard": 5,
    "rope_50ft": 1,
    "holy_water": 25,
    "dagger": 3,
    "sword": 10,
    "leather_armor": 20,
    "chain_mail": 40,
    "plate_mail": 60,
    "shield": 10,
}


# ── behavior 1: price list (§2) ─────────────────────────────────────────────


def test_price_list_values_are_positive_integers() -> None:
    """WHEN reading PRICE_LIST THEN every price is a positive integer."""
    assert PRICE_LIST
    for key, price in PRICE_LIST.items():
        assert isinstance(price, int), key
        assert price > 0, key


def test_price_list_anchor_items_match_spec() -> None:
    """WHEN reading the §2 anchor items THEN their prices match the listed gp values."""
    for key, expected in _ANCHOR_PRICES.items():
        assert PRICE_LIST[key] == expected


# ── behavior 2: starting gold (§5) ──────────────────────────────────────────


def test_starting_gold_in_3d6x10_range() -> None:
    """WHEN rolling starting gold THEN the result is within the inclusive [30, 180] range."""
    for seed in range(200):
        gold = starting_gold(random.Random(seed))
        assert 30 <= gold <= 180
        assert gold % 10 == 0


def test_starting_gold_is_deterministic_for_a_seed() -> None:
    """WHEN the seeded RNG is fixed THEN starting_gold returns the same value each call."""
    assert starting_gold(random.Random(1234)) == starting_gold(random.Random(1234))


# ── behavior 3: Trader buy payout (§3.1) ────────────────────────────────────


def test_trader_pays_half_list_for_priced_loot() -> None:
    """WHEN the Trader buys priced loot THEN it pays floor(list_price x 0.5)."""
    assert trader_payout(list_price=10) == 5
    assert trader_payout(list_price=25) == 12  # floor(12.5)
    assert trader_payout(list_price=3) == 1  # floor(1.5)


def test_trader_pays_full_appraised_value_for_gems() -> None:
    """WHEN the Trader buys a gem THEN it pays the full appraised gp value (no haircut)."""
    assert trader_payout(gem_value=500) == 500
    # A gem value takes precedence over any list price.
    assert trader_payout(list_price=10, gem_value=500) == 500


def test_trader_refuses_item_with_no_value() -> None:
    """WHEN an item has no list price and no gem value THEN the Trader cannot buy it."""
    assert trader_payout() is None
    assert trader_payout(list_price=None, gem_value=None) is None


# ── behavior 4: XP-on-secure accounting (§6) ────────────────────────────────


def test_secure_xp_grants_full_amount_when_nothing_credited() -> None:
    """WHEN no value has yet been credited THEN secure_xp grants the whole secured total."""
    grant, credited = secure_xp(100, 0)
    assert grant == 100
    assert credited == 100


def test_secure_xp_grants_zero_for_unchanged_total() -> None:
    """WHEN the secured total is unchanged THEN a second call grants 0 (no double credit)."""
    grant, credited = secure_xp(100, 100)
    assert grant == 0
    assert credited == 100


def test_secure_xp_grants_only_the_delta_on_a_higher_total() -> None:
    """WHEN the secured total rises THEN secure_xp grants only the new delta."""
    grant, credited = secure_xp(150, 100)
    assert grant == 50
    assert credited == 150


def test_secure_xp_new_credited_equals_running_total() -> None:
    """WHEN secure_xp resolves THEN the new credited counter equals the running secured total."""
    _, credited = secure_xp(250, 100)
    assert credited == 250


def test_secure_xp_never_returns_a_negative_grant() -> None:
    """WHEN the total is below what is already credited THEN the grant is clamped to 0."""
    grant, credited = secure_xp(40, 100)
    assert grant == 0
    # The counter is monotonic — it never drops below what was already credited.
    assert credited == 100


# ── behavior 5: buy arithmetic (§3.2) ───────────────────────────────────────


def test_buy_refuses_when_coin_below_price() -> None:
    """WHEN coin < price THEN the purchase is unaffordable and no coin is debited."""
    success, new_coin = purchase(coin=5, price=10)
    assert success is False
    assert new_coin == 5


def test_buy_debits_exactly_the_price_on_success() -> None:
    """WHEN coin >= price THEN exactly price is debited and the new balance is non-negative."""
    success, new_coin = purchase(coin=10, price=10)
    assert success is True
    assert new_coin == 0
    success, new_coin = purchase(coin=50, price=20)
    assert success is True
    assert new_coin == 30


# ── behavior 6: deposit / withdraw arithmetic (§4) ──────────────────────────


def test_deposit_is_lossless_with_zero_fee() -> None:
    """WHEN BANK_DEPOSIT_FEE_PCT is 0 THEN deposit conserves coin + bank_balance exactly."""
    success, new_coin, new_bank = deposit(coin=100, bank_balance=20, amount=60)
    assert success is True
    assert new_coin == 40
    assert new_bank == 80
    assert new_coin + new_bank == 100 + 20


def test_deposit_fee_is_removed_as_a_sink() -> None:
    """WHEN a deposit fee applies THEN the balance rises by amount - floor(amount x fee)."""
    success, new_coin, new_bank = deposit(coin=100, bank_balance=0, amount=50, fee_pct=0.1)
    assert success is True
    assert new_coin == 50  # full amount leaves the purse
    assert new_bank == 45  # 50 - floor(50 * 0.1) = 50 - 5
    # Total is NOT conserved — the 5 gp fee is removed as a sink.
    assert new_coin + new_bank == 95


def test_deposit_refuses_overdraft() -> None:
    """WHEN the deposit amount exceeds carried coin THEN it is refused and nothing changes."""
    success, new_coin, new_bank = deposit(coin=30, bank_balance=10, amount=40)
    assert success is False
    assert new_coin == 30
    assert new_bank == 10


def test_withdraw_refuses_overdraft() -> None:
    """WHEN the withdraw amount exceeds the bank balance THEN it is refused and nothing changes."""
    success, new_coin, new_bank = withdraw(coin=10, bank_balance=30, amount=40)
    assert success is False
    assert new_coin == 10
    assert new_bank == 30


def test_balances_never_go_negative() -> None:
    """WHEN any deposit/withdraw resolves THEN neither coin nor bank_balance is negative."""
    # Withdraw conserves the total and never produces a negative purse/balance.
    success, new_coin, new_bank = withdraw(coin=0, bank_balance=100, amount=100)
    assert success is True
    assert new_coin == 100
    assert new_bank == 0
    assert new_coin >= 0
    assert new_bank >= 0
    # A non-positive amount is rejected outright (no negative-amount exploit).
    assert deposit(coin=10, bank_balance=0, amount=0)[0] is False
    assert withdraw(coin=10, bank_balance=10, amount=-5)[0] is False
