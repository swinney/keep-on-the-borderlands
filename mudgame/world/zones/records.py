"""Record shapes for static zone data (zones spec R1 §1).

These TypedDicts document the *data, not behaviour* contract every zone package
shares. They are pure typing aids — no Evennia import — so zone data validates
without booting the server. Optional keys use ``NotRequired``.
"""

from __future__ import annotations

from typing import NotRequired, TypedDict


class RoomRecord(TypedDict):
    """A single room. ``coords`` only appears on xyzgrid zones (Wilderness)."""

    key: str
    name: str
    desc: str
    zone: str
    dark: NotRequired[bool]
    no_recall: NotRequired[bool]
    coords: NotRequired[tuple[int, int]]
    details: NotRequired[dict[str, str]]


# ``from`` is a Python keyword, so ExitRecord uses the functional TypedDict
# syntax to keep the field name matching the spec exactly. ``to`` may be a bare
# intra-zone room key or a ``"<zone>:<key>"`` inter-zone target.
ExitRecord = TypedDict(
    "ExitRecord",
    {
        "from": str,
        "dir": str,
        "to": str,
        "aliases": NotRequired[list[str]],
        "locked": NotRequired[bool],
        "key_item": NotRequired[str],
    },
)


class MobRecord(TypedDict):
    """A faction-tagged stat block (ascending AC; arch §5.1)."""

    key: str
    name: str
    faction: str
    level: int
    hd: str
    ac: int
    attacks: str
    morale: int
    treasure: NotRequired[str]
    is_leader: NotRequired[bool]
    leader_role: NotRequired[str]


class SpawnRecord(TypedDict):
    """A spawn point feeding the repop manager (R3)."""

    room: str
    template: str
    count: int
    respawn_seconds: int
    is_leader: NotRequired[bool]
    leader_role: NotRequired[str]


class NpcRecord(TypedDict):
    """A static shop / quest / service NPC."""

    key: str
    name: str
    sdesc: str
    role: str
    inventory: NotRequired[list[str]]
    dialogue: NotRequired[dict[str, str]]
    quests: NotRequired[list[str]]
