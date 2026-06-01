"""Engine / command economy tests (R-econ / docs/specs/economy.md §9 behaviors 7-11).

These exercise the live Evennia layer (pytest-django): the ``buy``/``sell``
commands at the shop vendors, the ``deposit``/``withdraw``/``balance`` commands
at the bank, the XP-on-secure trigger, and the death-safety of the bank balance.
"""

from __future__ import annotations

from typing import Any

import pytest
from evennia.utils import create

from commands.economy import (
    CmdBuy,
    CmdDeposit,
    CmdSell,
    CmdWithdraw,
)


def _run(cmd: Any, caller: Any, args: str = "") -> list[str]:
    """Execute a command's parse()+func() synchronously, capturing caller.msg output."""
    messages: list[str] = []
    caller.msg = lambda text="", **_kw: messages.append(str(text))
    cmd.caller = caller
    cmd.cmdstring = cmd.key
    cmd.args = args
    cmd.raw_string = f"{cmd.key}{args}"
    cmd.parse()
    cmd.func()
    return messages


def _shop_room(room_key: str, name: str) -> Any:
    """Create a keep-zone shop room tagged with ``room_key``."""
    room = create.create_object("typeclasses.rooms.Room", key=name)
    room.db.zone = "keep"
    room.db.room_key = room_key
    return room


# ── behavior 7: buy command (§3.2, §8) ──────────────────────────────────────


@pytest.mark.django_db
def test_buy_creates_item_and_debits_price() -> None:
    """WHEN a player buys a stocked item they can afford THEN it spawns and price is debited."""
    room = _shop_room("provisioner", "eco-prov-buy")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter", key="eco-buyer", location=room
    )
    try:
        char.db.coin = 50
        _run(CmdBuy(), char, " torch")  # torch costs 1 gp
        assert char.db.coin == 49
        bought = [obj for obj in char.contents if obj.db.list_key == "torch"]
        assert len(bought) == 1
    finally:
        char.delete()
        room.delete()


@pytest.mark.django_db
def test_buy_refused_when_unaffordable() -> None:
    """WHEN a player cannot afford an item THEN buy is refused and coin is unchanged."""
    room = _shop_room("armorer", "eco-arm-buy")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter", key="eco-poor", location=room
    )
    try:
        char.db.coin = 5  # plate_mail costs 60
        messages = _run(CmdBuy(), char, " plate_mail")
        assert char.db.coin == 5
        assert not list(char.contents)
        assert any("afford" in m.lower() for m in messages)
    finally:
        char.delete()
        room.delete()


@pytest.mark.django_db
def test_buy_refused_when_item_not_in_stock() -> None:
    """WHEN the vendor does not stock the item THEN buy is refused with 'I don't deal in that'."""
    room = _shop_room("provisioner", "eco-prov-stock")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter", key="eco-wrongshop", location=room
    )
    try:
        char.db.coin = 100
        messages = _run(CmdBuy(), char, " sword")  # sword is a weaponsmith item
        assert char.db.coin == 100
        assert not list(char.contents)
        assert any("don't deal" in m.lower() for m in messages)
    finally:
        char.delete()
        room.delete()


# ── behavior 8: sell command (§3.1, §8) ─────────────────────────────────────


@pytest.mark.django_db
def test_sell_at_trader_removes_item_and_credits_half() -> None:
    """WHEN a player sells priced loot to the Trader THEN it is removed and 50% is credited."""
    room = _shop_room("trader", "eco-trader-sell")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter", key="eco-seller", location=room
    )
    item = create.create_object("typeclasses.objects.Object", key="sword", location=char)
    item.db.list_key = "sword"  # list price 10 → payout floor(10*0.5) = 5
    try:
        char.db.coin = 0
        _run(CmdSell(), char, " sword")
        assert char.db.coin == 5
        assert not list(char.contents)
    finally:
        char.delete()
        room.delete()


@pytest.mark.django_db
def test_sell_refuses_item_with_no_sale_value() -> None:
    """WHEN an item has no sale value THEN the Trader refuses and nothing changes."""
    room = _shop_room("trader", "eco-trader-novalue")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter", key="eco-junk", location=room
    )
    item = create.create_object("typeclasses.objects.Object", key="trinket", location=char)
    try:
        char.db.coin = 0
        messages = _run(CmdSell(), char, " trinket")
        assert char.db.coin == 0
        assert item in list(char.contents)
        assert any("no use" in m.lower() for m in messages)
    finally:
        char.delete()
        room.delete()


# ── behavior 9: bank commands, room-scoped (§4, §8) ─────────────────────────


@pytest.mark.django_db
def test_deposit_moves_coin_to_bank_in_bank_room() -> None:
    """WHEN a player deposits in the bank room THEN coin moves to bank_balance (conserved)."""
    room = _shop_room("bank", "eco-bank-dep")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter", key="eco-depositor", location=room
    )
    try:
        char.db.coin = 100
        char.db.bank_balance = 0
        _run(CmdDeposit(), char, " 60")
        assert char.db.coin == 40
        assert char.db.bank_balance == 60
        assert char.db.coin + char.db.bank_balance == 100
    finally:
        char.delete()
        room.delete()


@pytest.mark.django_db
def test_withdraw_moves_bank_to_coin_in_bank_room() -> None:
    """WHEN a player withdraws in the bank room THEN bank_balance moves to coin (conserved)."""
    room = _shop_room("bank", "eco-bank-wd")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter", key="eco-withdrawer", location=room
    )
    try:
        char.db.coin = 10
        char.db.bank_balance = 90
        _run(CmdWithdraw(), char, " 40")
        assert char.db.coin == 50
        assert char.db.bank_balance == 50
        assert char.db.coin + char.db.bank_balance == 100
    finally:
        char.delete()
        room.delete()


@pytest.mark.django_db
def test_bank_commands_refused_outside_bank_room() -> None:
    """WHEN deposit/withdraw are used outside the bank room THEN they are refused, no change."""
    room = _shop_room("provisioner", "eco-notbank")  # not the bank
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter", key="eco-notbank-pc", location=room
    )
    try:
        char.db.coin = 100
        char.db.bank_balance = 0
        _run(CmdDeposit(), char, " 50")
        _run(CmdWithdraw(), char, " 50")
        assert char.db.coin == 100
        assert char.db.bank_balance == 0
    finally:
        char.delete()
        room.delete()


@pytest.mark.django_db
def test_bank_commands_refuse_overdraft() -> None:
    """WHEN a deposit/withdraw would overdraw THEN it is refused and balances are unchanged."""
    room = _shop_room("bank", "eco-bank-overdraft")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter", key="eco-overdraft-pc", location=room
    )
    try:
        char.db.coin = 30
        char.db.bank_balance = 20
        _run(CmdDeposit(), char, " 40")  # only 30 coin
        assert char.db.coin == 30
        assert char.db.bank_balance == 20
        _run(CmdWithdraw(), char, " 40")  # only 20 banked
        assert char.db.coin == 30
        assert char.db.bank_balance == 20
    finally:
        char.delete()
        room.delete()


# ── behavior 10: XP-on-secure trigger (§6) ──────────────────────────────────


@pytest.mark.django_db
def test_depositing_coin_grants_secured_xp_once() -> None:
    """WHEN coin is deposited THEN secured XP is granted once per gp via the credited counter."""
    room = _shop_room("bank", "eco-secure-dep")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter", key="eco-secure-pc", location=room
    )
    try:
        char.db.coin = 100
        char.db.bank_balance = 0
        char.db.secured_xp_credited = 0
        _run(CmdDeposit(), char, " 100")
        assert int(char.traits.xp.current) == 100
        assert int(char.db.secured_xp_credited) == 100
        # Withdraw and re-deposit the same coin → no further XP.
        _run(CmdWithdraw(), char, " 100")
        _run(CmdDeposit(), char, " 100")
        assert int(char.traits.xp.current) == 100
    finally:
        char.delete()
        room.delete()


@pytest.mark.django_db
def test_entering_keep_with_coin_grants_secured_xp_once() -> None:
    """WHEN a player carries coin into a Keep room THEN secured XP is granted once per gp."""
    wild = create.create_object("typeclasses.rooms.Room", key="eco-wild")  # zone None
    keep = _shop_room("inner_bailey", "eco-keep-entry")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter", key="eco-enter-pc", location=wild
    )
    try:
        char.db.coin = 50
        char.db.bank_balance = 0
        char.db.secured_xp_credited = 0
        char.move_to(keep, quiet=True)
        assert int(char.traits.xp.current) == 50
        assert int(char.db.secured_xp_credited) == 50
    finally:
        char.delete()
        keep.delete()
        wild.delete()


@pytest.mark.django_db
def test_resecuring_same_coin_grants_no_further_xp() -> None:
    """WHEN the same coin is re-secured THEN no additional XP is granted."""
    wild = create.create_object("typeclasses.rooms.Room", key="eco-wild-2")
    keep = _shop_room("inner_bailey", "eco-keep-entry-2")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter", key="eco-reenter-pc", location=wild
    )
    try:
        char.db.coin = 50
        char.db.secured_xp_credited = 0
        char.move_to(keep, quiet=True)
        assert int(char.traits.xp.current) == 50
        # Leave and return with the same coin → no new XP.
        char.move_to(wild, quiet=True)
        char.move_to(keep, quiet=True)
        assert int(char.traits.xp.current) == 50
    finally:
        char.delete()
        keep.delete()
        wild.delete()


# ── behavior 11: bank balance is death-safe (§4, cross-check tests/death) ────


@pytest.mark.django_db
def test_bank_balance_survives_death_and_loot() -> None:
    """WHEN a character dies and is looted THEN its full bank_balance is retained."""
    room = create.create_object("typeclasses.rooms.Room", key="eco-death-room")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter", key="eco-death-pc", location=room
    )
    try:
        char.db.coin = 50
        char.db.bank_balance = 100
        char.apply_damage(9999)  # lethal → at_death() → corpse + default death
        # Bank balance is never in the corpse (death.md §3) and is untouched.
        assert char.db.bank_balance == 100
        # Carried coin went to the corpse, not the bank.
        assert int(char.db.coin or 0) == 0
    finally:
        # Delete children (corpse + any gear) before parents so Evennia never
        # needs to relocate them to a now-deleted home (mirrors tests/death).
        for obj in list(room.contents):
            for child in list(obj.contents):
                child.delete()
            obj.delete()
        room.delete()
