"""Economy Evennia layer (docs/specs/economy.md §5, §6).

Wires the pure money core (``world.rules.economy``) to live characters: the
XP-on-secure trigger (§6) and the starting-gold grant (§5). Kept thin — all
arithmetic lives in the pure core; this module only reads/writes character
state and applies the results.
"""

from __future__ import annotations

import random
from typing import Any

from world.rules.economy import secure_xp, starting_gold

KEEP_ZONE = "keep"


def secure_treasure(character: Any) -> int:
    """Grant XP for any newly-secured treasure (§6); return the XP granted.

    "Secured" value is the bank balance plus — only while the character stands
    in a ``keep``-zone room — the coin carried. A per-character monotonic
    counter (``db.secured_xp_credited``) ensures each gp converts to XP once, so
    re-depositing or re-entering the Keep with the same coin grants nothing.
    """
    location = character.location
    in_keep = bool(location is not None and location.db.zone == KEEP_ZONE)
    coin = int(character.db.coin or 0)
    bank = int(character.db.bank_balance or 0)
    total_secured = bank + (coin if in_keep else 0)
    credited = int(character.db.secured_xp_credited or 0)
    grant, new_credited = secure_xp(total_secured, credited)
    if grant > 0:
        character.traits.xp.current = int(character.traits.xp.current) + grant
        character.db.secured_xp_credited = new_credited
        character.msg(f"You secure your treasure and gain {grant} experience.")
    return grant


def grant_starting_gold(character: Any, rng: random.Random | None = None) -> int:
    """Roll 3d6x10 and credit it to the character's carried coin (§5); return the amount."""
    gold = starting_gold(rng if rng is not None else random.Random())
    character.db.coin = int(character.db.coin or 0) + gold
    return gold
