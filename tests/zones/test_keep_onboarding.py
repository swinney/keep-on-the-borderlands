"""M7 exit acceptance: a new character spawns, equips, hires, and rests.

The Keep is the onboarding hub. This suite boots Evennia, builds the Keep, and
drives the headline first-session loop end-to-end against the real commands —
starting gold (economy.md §5), shop buy (economy.md §8), tavern hire
(henchmen.md §1), and rest/memorization in a safe Keep room (zones/keep.md R8,
combat.md §5). It is the integration check that these subsystems compose inside
the live zone, not just in isolation.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any
from unittest.mock import patch

import pytest
from evennia.utils import create
from evennia.utils.search import search_object_by_tag

from commands.economy import CmdBuy
from commands.henchmen import CmdHire
from commands.spells import CmdRest
from world.economy import grant_starting_gold
from world.henchmen.config import ROSTER
from world.rules.economy import PRICE_LIST
from world.zones import keep
from world.zones.builder import EXIT_CATEGORY, NPC_CATEGORY, ROOM_CATEGORY

# Starting-gold bounds (3d6x10) per economy.md §5 / its acceptance criteria.
STARTING_GOLD_MIN = 30
STARTING_GOLD_MAX = 180

CHARACTER_TYPECLASS = "typeclasses.characters.PlayerCharacter"


def _find_room(room_key: str) -> Any:
    matches = search_object_by_tag(f"keep:{room_key}", category=ROOM_CATEGORY)
    return matches[0] if matches else None


def _run(cmd_cls: Any, caller: Any, args: str = "") -> None:
    """Execute an Evennia command against ``caller`` as the engine would."""
    cmd = cmd_cls()
    cmd.caller = caller
    cmd.cmdstring = cmd_cls.key
    cmd.raw_string = f"{cmd_cls.key} {args}".strip()
    cmd.args = f" {args}" if args else ""
    cmd.parse()
    cmd.func()


@pytest.fixture
def built_keep() -> Iterator[None]:
    """Build the Keep, yield, then tear down every room/exit/NPC it created."""
    keep.build()
    try:
        yield
    finally:
        for npc in search_object_by_tag(category=NPC_CATEGORY):
            npc.delete()
        for exit_ in search_object_by_tag(category=EXIT_CATEGORY):
            exit_.delete()
        for room in search_object_by_tag(category=ROOM_CATEGORY):
            room.delete()


@pytest.mark.django_db
def test_new_character_spawns_equips_hires_and_rests(built_keep: None) -> None:
    """The full M7 first-session loop: spawn -> equip -> hire -> rest."""
    char = create.create_object(CHARACTER_TYPECLASS, key="Newcomer")
    henchman = None
    try:
        # ── spawns: arrive at the recall point with rolled starting gold ──
        char.location = _find_room("inner_bailey")
        assert char.location is not None, "Inner Bailey (recall point) is built"
        gold = grant_starting_gold(char)
        assert STARTING_GOLD_MIN <= gold <= STARTING_GOLD_MAX
        assert char.db.coin == gold

        # ── equips: buy gear at the provisioner ──
        char.location = _find_room("provisioner")
        coin_before_buy = char.db.coin
        _run(CmdBuy, char, "torch")
        bought = [o for o in char.contents if o.db.list_key == "torch"]
        assert bought, "the purchased torch lands in the buyer's inventory"
        assert char.db.coin == coin_before_buy - PRICE_LIST["torch"]

        # ── hires: recruit the first roster henchman at the tavern ──
        recruit = ROSTER[0]
        char.location = _find_room("tavern")
        char.traits.cha.base = 16  # comfortably above the retainer cap of 1
        coin_before_hire = char.db.coin
        assert coin_before_hire >= recruit.hire_fee, "starting gold affords a hire"
        # Pin the 2d6 reaction roll above REACTION_REFUSE_AT_OR_BELOW (5).
        with patch("commands.henchmen.dice.roll", return_value=9):
            _run(CmdHire, char, recruit.name)
        party = [o for o in char.location.contents if o.db.employer == char]
        assert len(party) == 1, "exactly one henchman joins the party"
        henchman = party[0]
        assert henchman.db.roster_key == recruit.key
        assert char.db.coin == coin_before_hire - recruit.hire_fee

        # ── rests: memorize spells in a safe Keep room ──
        char.location = _find_room("inn")
        char.db.char_class = "magic_user"
        char.traits.level.base = 1
        char.db.spellbook = ["magic missile"]
        _run(CmdRest, char)
        assert char.db.memorized_spells == ["magic missile"]
    finally:
        if henchman is not None:
            henchman.delete()
        char.delete()


@pytest.mark.django_db
def test_rest_memorizes_in_any_safe_keep_room(built_keep: None) -> None:
    """zones/keep.md R8: the inn *or any safe Keep room* permits memorization."""
    char = create.create_object(CHARACTER_TYPECLASS, key="Acolyte")
    try:
        char.location = _find_room("inner_bailey")
        char.db.char_class = "cleric"
        char.traits.level.base = 2  # L2 cleric has one first-level slot
        _run(CmdRest, char)
        assert len(char.db.memorized_spells or []) == 1
    finally:
        char.delete()


@pytest.mark.django_db
def test_signup_spawns_character_at_recall_point(built_keep: None) -> None:
    """A character created via the real account-signup path spawns at the Keep.

    This exercises ``Account.create_character`` — the path a `create <name>`
    player actually takes — not a bare ``create_object``. The distinction is the
    whole point (field-log §5.18): ``create_character`` assigns
    ``location=START_LOCATION`` (Evennia's default → Limbo) *before* the character
    is returned, so a fix in ``Character.at_object_creation`` is overwritten and
    real players land in Limbo. The fix lives in ``Account.at_post_create_character``,
    which runs after the location is set; this test drives that path end to end.
    """
    recall = _find_room("inner_bailey")
    assert recall is not None, "Inner Bailey (recall point) is built"

    account = create.create_account("Newcomer-acct", email="", password="passw0rd-xyz-1")
    char, errors = account.create_character(key="Newcomer-char")
    try:
        assert not errors, errors
        assert char is not None
        assert char.location == recall, "signup spawns the character at the Inner Bailey"
    finally:
        if char is not None:
            char.delete()
        account.delete()
