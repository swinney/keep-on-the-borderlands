"""Economy commands: buy, sell, list, deposit, withdraw, balance.

docs/specs/economy.md §8. Shops are realized as room-scoped vendors: a room's
``db.room_key`` (set by the zone builder) names the vendor — ``provisioner``,
``armorer``, ``weaponsmith``, ``trader`` for shops, and ``bank`` for the
moneychanger. The pure money math lives in ``world.rules.economy``; these
commands only validate scope, move items, and read/write coin and balance,
never leaving a balance negative or creating/destroying money outside an
explicit fee or a shop's buy/sell spread.
"""

from __future__ import annotations

from typing import Any, ClassVar

from evennia.commands.command import Command
from evennia.utils import create

from world.economy import secure_treasure
from world.rules.economy import (
    PRICE_LIST,
    SHOP_STOCK,
    deposit,
    normalize_item_key,
    purchase,
    trader_payout,
    withdraw,
)

BANK_ROOM_KEY = "bank"
TRADER_ROOM_KEY = "trader"
ITEM_TYPECLASS = "typeclasses.objects.Object"


def _room_key(caller: Any) -> str:
    """Return the caller's room ``room_key`` ('' when roomless or untagged)."""
    location = caller.location
    if location is None:
        return ""
    return str(location.db.room_key or "")


class CmdBuy(Command):  # type: ignore[misc]
    """Buy an item from the shop in your current room.

    Usage:
      buy <item>

    Costs the item's full list price; refused if you can't afford it or the
    vendor doesn't stock it.
    """

    key = "buy"
    aliases: ClassVar[list[str]] = []
    help_category = "Economy"

    def parse(self) -> None:
        self.item_name = self.args.strip()

    def func(self) -> None:
        caller = self.caller
        stock = SHOP_STOCK.get(_room_key(caller))
        if stock is None:
            caller.msg("There is nothing to buy here.")
            return
        if not self.item_name:
            caller.msg("Buy what?")
            return

        item_key = normalize_item_key(self.item_name)
        if item_key not in stock:
            caller.msg("I don't deal in that.")
            return

        price = PRICE_LIST[item_key]
        coin = int(caller.db.coin or 0)
        success, new_coin = purchase(coin, price)
        if not success:
            caller.msg(f"You can't afford that ({price} gp).")
            return

        caller.db.coin = new_coin
        item = create.create_object(ITEM_TYPECLASS, key=item_key, location=caller)
        item.db.list_key = item_key
        caller.msg(f"You buy {item_key} for {price} gp. You have {new_coin} gp left.")


class CmdSell(Command):  # type: ignore[misc]
    """Sell loot to the Trader.

    Usage:
      sell <item>

    Pays 50% of list value for priced loot and the full appraised value for
    gems. Items with no sale value are refused.
    """

    key = "sell"
    aliases: ClassVar[list[str]] = []
    help_category = "Economy"

    def parse(self) -> None:
        self.item_name = self.args.strip()

    def func(self) -> None:
        caller = self.caller
        if _room_key(caller) != TRADER_ROOM_KEY:
            caller.msg("There is no one here to buy your loot.")
            return
        if not self.item_name:
            caller.msg("Sell what?")
            return

        item = caller.search(self.item_name, location=caller, quiet=True)
        item = item[0] if item else None
        if item is None:
            caller.msg(f"You aren't carrying '{self.item_name}'.")
            return

        gem_value = item.db.gem_value
        list_key = item.db.list_key
        list_price = PRICE_LIST.get(list_key) if list_key else None
        payout = trader_payout(
            list_price=list_price,
            gem_value=int(gem_value) if gem_value is not None else None,
        )
        if payout is None:
            caller.msg("The trader has no use for that.")
            return

        sold_name = item.key
        item.delete()
        caller.db.coin = int(caller.db.coin or 0) + payout
        caller.msg(f"You sell {sold_name} for {payout} gp.")


class CmdList(Command):  # type: ignore[misc]
    """List the wares of the shop in your current room.

    Usage:
      list
    """

    key = "list"
    aliases: ClassVar[list[str]] = ["wares"]
    help_category = "Economy"

    def func(self) -> None:
        caller = self.caller
        stock = SHOP_STOCK.get(_room_key(caller))
        if stock is None:
            caller.msg("There is no shop here.")
            return
        lines = ["Wares for sale:"]
        lines.extend(f"  {key} - {PRICE_LIST[key]} gp" for key in stock)
        caller.msg("\n".join(lines))


class CmdDeposit(Command):  # type: ignore[misc]
    """Deposit coin into the Keep's vault (bank room only).

    Usage:
      deposit <amount>
    """

    key = "deposit"
    aliases: ClassVar[list[str]] = []
    help_category = "Economy"

    def parse(self) -> None:
        self.amount_text = self.args.strip()

    def func(self) -> None:
        caller = self.caller
        if _room_key(caller) != BANK_ROOM_KEY:
            caller.msg("There is no bank here.")
            return
        amount = _parse_amount(caller, self.amount_text)
        if amount is None:
            return

        coin = int(caller.db.coin or 0)
        bank = int(caller.db.bank_balance or 0)
        success, new_coin, new_bank = deposit(coin, bank, amount)
        if not success:
            caller.msg("You don't have that much coin to deposit.")
            return

        caller.db.coin = new_coin
        caller.db.bank_balance = new_bank
        caller.msg(f"You deposit {amount} gp. Balance: {new_bank} gp; carried: {new_coin} gp.")
        # Banked coin is secured value → may grant XP-on-secure (§6).
        secure_treasure(caller)


class CmdWithdraw(Command):  # type: ignore[misc]
    """Withdraw coin from the Keep's vault (bank room only).

    Usage:
      withdraw <amount>
    """

    key = "withdraw"
    aliases: ClassVar[list[str]] = []
    help_category = "Economy"

    def parse(self) -> None:
        self.amount_text = self.args.strip()

    def func(self) -> None:
        caller = self.caller
        if _room_key(caller) != BANK_ROOM_KEY:
            caller.msg("There is no bank here.")
            return
        amount = _parse_amount(caller, self.amount_text)
        if amount is None:
            return

        coin = int(caller.db.coin or 0)
        bank = int(caller.db.bank_balance or 0)
        success, new_coin, new_bank = withdraw(coin, bank, amount)
        if not success:
            caller.msg("Your balance is too low for that withdrawal.")
            return

        caller.db.coin = new_coin
        caller.db.bank_balance = new_bank
        caller.msg(f"You withdraw {amount} gp. Balance: {new_bank} gp; carried: {new_coin} gp.")


class CmdBalance(Command):  # type: ignore[misc]
    """Show your carried coin and bank balance (bank room only).

    Usage:
      balance
    """

    key = "balance"
    aliases: ClassVar[list[str]] = []
    help_category = "Economy"

    def func(self) -> None:
        caller = self.caller
        if _room_key(caller) != BANK_ROOM_KEY:
            caller.msg("There is no bank here.")
            return
        coin = int(caller.db.coin or 0)
        bank = int(caller.db.bank_balance or 0)
        caller.msg(f"Carried: {coin} gp. Banked: {bank} gp.")


def _parse_amount(caller: Any, text: str) -> int | None:
    """Parse a positive integer gp amount, messaging the caller on bad input."""
    if not text:
        caller.msg("Specify an amount.")
        return None
    try:
        amount = int(text)
    except ValueError:
        caller.msg("Specify a whole number of gold pieces.")
        return None
    if amount <= 0:
        caller.msg("The amount must be positive.")
        return None
    return amount
