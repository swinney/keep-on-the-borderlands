"""Engine tests for the tavern roster + hire commands (henchmen.md §1).

These exercise the live Evennia layer (pytest-django): ``roster`` lists the
recruits and is gated to the tavern; ``hire`` resolves the OSE reaction roll,
charges the fee, enforces the CHA retainer cap, and adds a Henchman to the
party. The reaction dice are patched so outcomes are deterministic.
"""

from __future__ import annotations

import contextlib
from typing import Any

import pytest
from evennia.utils import create

from commands.henchmen import CmdHire, CmdRoster
from world.henchmen.config import ROSTER
from world.rules import dice


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


def _tavern(name: str) -> Any:
    room = create.create_object("typeclasses.rooms.Room", key=name)
    room.db.zone = "keep"
    room.db.room_key = "tavern"
    return room


def _player(name: str, room: Any, *, cha: int = 12, coin: int = 0) -> Any:
    char = create.create_object("typeclasses.characters.PlayerCharacter", key=name, location=room)
    char.traits.cha.base = cha
    char.db.coin = coin
    return char


def _force_reaction(monkeypatch: Any, total: int) -> None:
    """Pin the 2d6 reaction roll so ``reaction = total + cha modifier``.

    The command calls ``dice.roll`` through its module-level import of this same
    module, so patching the canonical function here affects the command too.
    """
    monkeypatch.setattr(dice, "roll", lambda notation, *, rng: total)


# ── roster command ──────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_roster_only_works_in_tavern() -> None:
    room = create.create_object("typeclasses.rooms.Room", key="rost-elsewhere")
    room.db.room_key = "outer_bailey"
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter", key="rost-nofun", location=room
    )
    try:
        messages = _run(CmdRoster(), char)
        assert any("tavern" in m.lower() for m in messages)
    finally:
        char.delete()
        room.delete()


@pytest.mark.django_db
def test_roster_lists_every_recruit() -> None:
    room = _tavern("rost-tavern")
    char = _player("rost-patron", room)
    try:
        text = "\n".join(_run(CmdRoster(), char))
        for entry in ROSTER:
            assert entry.name in text
    finally:
        char.delete()
        room.delete()


# ── hire command ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_successful_hire_creates_henchman_and_charges(monkeypatch: Any) -> None:
    room = _tavern("hire-ok-tavern")
    char = _player("hire-ok-patron", room, cha=12, coin=50)
    pip = ROSTER[0]  # Pip the torchbearer, 10 gp
    _force_reaction(monkeypatch, 11)  # 11 > refuse threshold → accepts
    try:
        _run(CmdHire(), char, f" {pip.name}")
        assert char.db.coin == 50 - pip.hire_fee
        hires = [obj for obj in room.contents if getattr(obj, "IS_HENCHMAN", False)]
        assert len(hires) == 1
        assert hires[0].db.employer == char
        assert hires[0].db.loyalty > 0
    finally:
        for obj in list(room.contents):
            with contextlib.suppress(Exception):
                obj.delete()
        room.delete()


@pytest.mark.django_db
def test_refused_hire_costs_nothing(monkeypatch: Any) -> None:
    room = _tavern("hire-no-tavern")
    char = _player("hire-no-patron", room, cha=12, coin=50)
    pip = ROSTER[0]
    _force_reaction(monkeypatch, 2)  # 2 ≤ refuse threshold → declines
    try:
        _run(CmdHire(), char, f" {pip.name}")
        assert char.db.coin == 50  # untouched
        assert not [obj for obj in room.contents if getattr(obj, "IS_HENCHMAN", False)]
    finally:
        for obj in list(room.contents):
            with contextlib.suppress(Exception):
                obj.delete()
        room.delete()


@pytest.mark.django_db
def test_hire_blocked_at_charisma_cap(monkeypatch: Any) -> None:
    room = _tavern("hire-cap-tavern")
    char = _player("hire-cap-patron", room, cha=12, coin=500)  # CHA 12 → cap 4
    _force_reaction(monkeypatch, 11)
    existing = []
    for i in range(4):
        h = create.create_object("typeclasses.npcs.Henchman", key=f"cap-h{i}", location=room)
        h.db.employer = char
        existing.append(h)
    try:
        messages = _run(CmdHire(), char, f" {ROSTER[0].name}")
        assert char.db.coin == 500  # no fee charged
        # still exactly the 4 pre-existing henchmen — none added
        assert len([o for o in room.contents if getattr(o, "IS_HENCHMAN", False)]) == 4
        assert any("retainer" in m.lower() or "charisma" in m.lower() for m in messages)
    finally:
        for obj in list(room.contents):
            with contextlib.suppress(Exception):
                obj.delete()
        room.delete()


@pytest.mark.django_db
def test_hire_unaffordable_refused(monkeypatch: Any) -> None:
    room = _tavern("hire-poor-tavern")
    char = _player("hire-poor-patron", room, cha=12, coin=10)
    acolyte = next(e for e in ROSTER if e.hire_fee == 100)  # too pricey
    _force_reaction(monkeypatch, 11)  # would accept, but can't pay
    try:
        messages = _run(CmdHire(), char, f" {acolyte.name}")
        assert char.db.coin == 10
        assert not [obj for obj in room.contents if getattr(obj, "IS_HENCHMAN", False)]
        assert any("afford" in m.lower() for m in messages)
    finally:
        for obj in list(room.contents):
            with contextlib.suppress(Exception):
                obj.delete()
        room.delete()
