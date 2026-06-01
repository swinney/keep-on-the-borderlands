"""Caves of Chaos zone tests — M9 kobold slice.

Derived from docs/specs/zones.md §6 and docs/specs/zones/caves.md. Pure-data
groups validate the static room/exit/mob/spawn data without booting Evennia;
the engine groups (pytest-django) verify build() materialises and links the
zone.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from typing import Any

import pytest

from world.factions.config import FACTIONS
from world.repop import config as repop_cfg
from world.zones import caves
from world.zones.caves import discovery
from world.zones.spawn_registry import spawn_points

# Aggregated zone data (ravine hub + every discovered tribe), exposed off the
# package now that rooms/exits/mobs/spawns live in per-tribe subpackages.
EXITS = caves.EXITS
MOB_TEMPLATES = caves.MOB_TEMPLATES
ROOMS = caves.ROOMS
SPAWNS = caves.SPAWNS

# Rooms that are part of a (dark) lair vs the open-air ravine spine.
RAVINE_ROOMS: frozenset[str] = frozenset({"ravine", "ravine_north", "ravine_mid", "ravine_south"})
KOBOLD_LAIR_ROOMS: frozenset[str] = frozenset(
    {
        "kobold_mouth",
        "kobold_guard",
        "kobold_kennels",
        "kobold_warren",
        "kobold_grotto",
        "kobold_den",
    }
)


# ---------------------------------------------------------------------------
# Group 1 — Standard zone interface
# ---------------------------------------------------------------------------


def test_zone_exposes_standard_interface() -> None:
    assert callable(caves.build)
    assert isinstance(caves.ROOMS, list)
    assert isinstance(caves.EXITS, list)
    assert isinstance(caves.MOB_TEMPLATES, list)
    assert isinstance(caves.SPAWNS, list)
    assert isinstance(caves.NPCS, list)
    assert caves.ZONE == "caves"


# ---------------------------------------------------------------------------
# Group 2 — Room / exit data integrity (zones spec §6: 2, 8)
# ---------------------------------------------------------------------------


def test_room_keys_unique() -> None:
    keys = [r["key"] for r in ROOMS]
    assert len(keys) == len(set(keys)), "duplicate room key in caves ROOMS"


def test_expected_rooms_present() -> None:
    keys = {r["key"] for r in ROOMS}
    assert keys >= RAVINE_ROOMS
    assert keys >= KOBOLD_LAIR_ROOMS


def test_no_dangling_intra_zone_exits() -> None:
    room_keys = {r["key"] for r in ROOMS}
    for exit_ in EXITS:
        assert exit_["from"] in room_keys, f"exit from unknown room {exit_['from']!r}"
        to = exit_["to"]
        if ":" in to:
            continue  # inter-zone target, validated separately
        assert to in room_keys, f"exit to unknown room {to!r}"


def test_inter_zone_exit_targets_wilderness_ravine_mouth() -> None:
    inter = [e for e in EXITS if ":" in e["to"]]
    assert inter, "caves should expose an inter-zone exit to the wilderness"
    assert any(e["to"] == "wilderness:ravine_mouth" for e in inter)


def test_lair_rooms_are_dark() -> None:
    by_key = {r["key"]: r for r in ROOMS}
    for key in KOBOLD_LAIR_ROOMS:
        assert by_key[key].get("dark") is True, f"{key} should be dark"


def test_ravine_rooms_are_lit() -> None:
    by_key = {r["key"]: r for r in ROOMS}
    for key in RAVINE_ROOMS:
        assert not by_key[key].get("dark"), f"open-air {key} should not be dark"


# ---------------------------------------------------------------------------
# Group 3 — Mob templates (zones spec §6: 3, 9)
# ---------------------------------------------------------------------------


def test_mob_factions_are_valid_ids() -> None:
    valid = set(FACTIONS.keys())
    for mob in MOB_TEMPLATES:
        assert mob["faction"] in valid, f"mob {mob['key']!r} bad faction {mob['faction']!r}"


def test_kobold_mobs_use_kobold_faction() -> None:
    assert all(m["faction"] == "kobold" for m in MOB_TEMPLATES)


def test_mob_ascending_ac_in_range() -> None:
    for mob in MOB_TEMPLATES:
        assert mob["ac"] >= 10, f"mob {mob['key']!r} AC {mob['ac']} below ascending base 10"


def test_mob_keys_unique() -> None:
    keys = [m["key"] for m in MOB_TEMPLATES]
    assert len(keys) == len(set(keys))


# ---------------------------------------------------------------------------
# Group 4 — Spawns + leadership (zones spec §6: 4, 5)
# ---------------------------------------------------------------------------


def test_spawn_templates_are_defined() -> None:
    mob_keys = {m["key"] for m in MOB_TEMPLATES}
    for spawn in SPAWNS:
        assert spawn["template"] in mob_keys, (
            f"spawn in {spawn['room']!r} references unknown template {spawn['template']!r}"
        )


def test_spawn_rooms_exist() -> None:
    room_keys = {r["key"] for r in ROOMS}
    for spawn in SPAWNS:
        assert spawn["room"] in room_keys, f"spawn references unknown room {spawn['room']!r}"


def test_kobold_tribe_has_exactly_one_chief_and_one_shaman() -> None:
    roles = [s.get("leader_role") for s in SPAWNS if s.get("is_leader")]
    assert roles.count("chief") == 1, "kobold tribe needs exactly one chief spawn"
    assert roles.count("shaman") == 1, "kobold tribe needs exactly one shaman spawn"


def test_leader_spawns_are_single_and_well_formed() -> None:
    for spawn in SPAWNS:
        if spawn.get("is_leader"):
            assert spawn.get("leader_role") in {"chief", "shaman"}
            assert spawn["count"] == 1, "a leader spawn must be a single mob"


# ---------------------------------------------------------------------------
# Group 5 — Repop spawn-point derivation (repop.md §1; pure, no Evennia)
# ---------------------------------------------------------------------------


def test_spawn_points_expand_count() -> None:
    """Each individual mob becomes its own SpawnPoint (per-mob respawn, §2)."""
    points = spawn_points("caves", SPAWNS, MOB_TEMPLATES)
    assert len(points) == sum(s["count"] for s in SPAWNS)


def test_spawn_point_ids_are_unique() -> None:
    points = spawn_points("caves", SPAWNS, MOB_TEMPLATES)
    ids = [p.spawn_id for p in points]
    assert len(ids) == len(set(ids))


def test_spawn_points_resolve_faction_from_template() -> None:
    """The point's faction is read from its mob template (§1), not invented."""
    faction_by_template = {m["key"]: m["faction"] for m in MOB_TEMPLATES}
    for point in spawn_points("caves", SPAWNS, MOB_TEMPLATES):
        assert point.faction == faction_by_template[point.mob_template]


def test_derived_points_have_one_chief_and_one_shaman_leader() -> None:
    """The two kobold leaders the R3 halt depends on survive derivation."""
    points = spawn_points("caves", SPAWNS, MOB_TEMPLATES)
    leaders = [p for p in points if p.is_leader]
    roles = [p.leader_role for p in leaders]
    assert roles.count("chief") == 1
    assert roles.count("shaman") == 1
    assert all(p.faction == "kobold" for p in leaders)


def test_spawn_point_room_is_zone_namespaced() -> None:
    """Rooms are ``<zone>:<key>`` so the manager can resolve them by tag (§1)."""
    for point in spawn_points("caves", SPAWNS, MOB_TEMPLATES):
        assert point.room.startswith("caves:")


def test_unknown_template_is_rejected() -> None:
    bad = [{"room": "kobold_den", "template": "dragon", "count": 1, "respawn_seconds": 900}]
    with pytest.raises(KeyError):
        spawn_points("caves", bad, MOB_TEMPLATES)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Engine tests (require Django) — build() materialises and links the zone
# ---------------------------------------------------------------------------


def _caves_rooms() -> list[Any]:
    from evennia.utils.search import search_object_by_tag  # noqa: PLC0415

    from world.zones.builder import ROOM_CATEGORY  # noqa: PLC0415

    return [r for r in search_object_by_tag(category=ROOM_CATEGORY) if r.db.zone == "caves"]


def _caves_exits() -> list[Any]:
    from evennia.utils.search import search_object_by_tag  # noqa: PLC0415

    from world.zones.builder import EXIT_CATEGORY  # noqa: PLC0415

    out = []
    for e in search_object_by_tag(category=EXIT_CATEGORY):
        loc = e.location
        if loc is not None and loc.db.zone == "caves":
            out.append(e)
    return out


def _find_caves_room(room_key: str) -> Any:
    from evennia.utils.search import search_object_by_tag  # noqa: PLC0415

    from world.zones.builder import ROOM_CATEGORY  # noqa: PLC0415

    matches = search_object_by_tag(f"caves:{room_key}", category=ROOM_CATEGORY)
    return matches[0] if matches else None


@pytest.fixture
def built_caves() -> Iterator[None]:
    """Build the caves alone (no wilderness), yield, then tear them down."""
    caves.build()
    try:
        yield
    finally:
        for exit_ in _caves_exits():
            exit_.delete()
        for room in _caves_rooms():
            room.delete()


@pytest.fixture
def built_wilderness_and_caves() -> Iterator[None]:
    """Build the Wilderness then the caves, yield, then tear both down."""
    from evennia.utils.search import search_object_by_tag  # noqa: PLC0415

    from world.zones import wilderness  # noqa: PLC0415
    from world.zones.builder import EXIT_CATEGORY, NPC_CATEGORY  # noqa: PLC0415

    wilderness.build()
    caves.build()
    try:
        yield
    finally:
        from evennia.contrib.grid.xyzgrid.xyzgrid import get_xyzgrid  # noqa: PLC0415

        # caves exits (incl. the return exit) and the forward 'enter' exit first.
        for exit_ in _caves_exits():
            exit_.delete()
        for exit_ in search_object_by_tag("wilderness:ravine_mouth:enter", category=EXIT_CATEGORY):
            exit_.delete()
        # Wilderness NPCs (the hermit) before remove_map (their home is a grid room).
        for npc in search_object_by_tag(category=NPC_CATEGORY):
            npc.delete()
        get_xyzgrid().remove_map("wilderness", remove_objects=True)
        for room in _caves_rooms():
            room.delete()


@pytest.mark.django_db
def test_build_creates_every_room(built_caves: None) -> None:
    built = {r.db.room_key for r in _caves_rooms()}
    assert built == {r["key"] for r in ROOMS}


@pytest.mark.django_db
def test_build_is_idempotent(built_caves: None) -> None:
    first_rooms = {r.id for r in _caves_rooms()}
    first_exits = {e.id for e in _caves_exits()}
    caves.build()
    assert {r.id for r in _caves_rooms()} == first_rooms
    assert {e.id for e in _caves_exits()} == first_exits


@pytest.mark.django_db
def test_lair_rooms_get_dark_flag(built_caves: None) -> None:
    from world.zones.builder import FLAG_CATEGORY  # noqa: PLC0415

    den = _find_caves_room("kobold_den")
    assert den is not None
    assert den.tags.has("dark", category=FLAG_CATEGORY)

    ravine = _find_caves_room("ravine")
    assert ravine is not None
    assert not ravine.tags.has("dark", category=FLAG_CATEGORY)


@pytest.mark.django_db
def test_ravine_tagged_as_wilderness_target(built_caves: None) -> None:
    """The ravine floor carries the caves:ravine_mouth alias the wilderness uses."""
    from evennia.utils.search import search_object_by_tag  # noqa: PLC0415

    from world.zones.builder import ROOM_CATEGORY  # noqa: PLC0415

    matches = search_object_by_tag("caves:ravine_mouth", category=ROOM_CATEGORY)
    assert len(matches) == 1
    assert matches[0].db.room_key == "ravine"


@pytest.mark.django_db
def test_internal_exit_is_reversible(built_caves: None) -> None:
    mouth = _find_caves_room("kobold_mouth")
    guard = _find_caves_room("kobold_guard")
    north = [e for e in mouth.exits if e.key == "n"]
    assert north and north[0].destination == guard
    south = [e for e in guard.exits if e.key == "s"]
    assert south and south[0].destination == mouth


@pytest.mark.django_db
def test_wilderness_to_caves_round_trip(built_wilderness_and_caves: None) -> None:
    """The ravine mouth links both ways: wilderness -> caves and back."""
    from evennia.utils.search import search_object_by_tag  # noqa: PLC0415

    from world.zones.builder import ROOM_CATEGORY  # noqa: PLC0415

    mouth_matches = search_object_by_tag("wilderness:ravine_mouth", category=ROOM_CATEGORY)
    assert mouth_matches
    mouth = mouth_matches[0]
    ravine = _find_caves_room("ravine")
    assert ravine is not None

    # Forward: wilderness ravine mouth -> caves ravine via 'enter'.
    enter = [e for e in mouth.exits if e.key == "enter"]
    assert enter, "no 'enter' exit from wilderness ravine_mouth into the caves"
    assert enter[0].destination == ravine

    # Return: caves ravine -> wilderness ravine mouth via 'w'.
    back = [e for e in ravine.exits if e.key == "w"]
    assert back, "no return exit from the caves ravine to the wilderness"
    assert back[0].destination == mouth


# ---------------------------------------------------------------------------
# Engine tests — chief + shaman wired to the leadership halt + rival scouting
# (repop.md §3-4; the M9 wiring this task delivers)
# ---------------------------------------------------------------------------


def _kobold_leaders() -> tuple[Any, Any]:
    """The derived chief and shaman SpawnPoints for the kobold tribe."""
    points = spawn_points("caves", SPAWNS, MOB_TEMPLATES)
    chief = next(p for p in points if p.leader_role == "chief")
    shaman = next(p for p in points if p.leader_role == "shaman")
    return chief, shaman


@pytest.fixture
def repop_and_factions() -> Iterator[tuple[Any, Any]]:
    """A registered repop_manager + faction_manager, torn down after the test."""
    from evennia.utils import create  # noqa: PLC0415

    repop = create.create_script("world.managers.repop_manager.RepopManager")
    factions = create.create_script("world.managers.faction_manager.FactionManager")
    repop.register_zone("caves", SPAWNS, MOB_TEMPLATES)
    try:
        yield repop, factions
    finally:
        repop.delete()
        factions.delete()


def _make_leader_mob(spawn_id: str, key: str, room: Any) -> Any:
    from evennia.utils import create  # noqa: PLC0415

    mob = create.create_object("typeclasses.npcs.Mob", key=key, location=room)
    mob.db.spawn_id = spawn_id
    mob.db.faction_id = "kobold"
    return mob


@pytest.mark.django_db
def test_killing_one_kobold_leader_does_not_halt(repop_and_factions: tuple[Any, Any]) -> None:
    """Dropping only the chief schedules its respawn but never halts the tribe."""
    from evennia.utils import create  # noqa: PLC0415

    repop, _ = repop_and_factions
    chief, _shaman = _kobold_leaders()
    room = create.create_object("typeclasses.rooms.Room", key="caves-halt-room-1")
    try:
        chief_mob = _make_leader_mob(chief.spawn_id, "Sharptooth", room)
        chief_mob.at_death()
        assert chief.spawn_id in (repop.db.respawn_at or {})
        assert "kobold" not in (repop.db.halted_until or {})
        assert not (repop.db.scouts or {})
    finally:
        room.delete()


@pytest.mark.django_db
def test_killing_both_kobold_leaders_halts_and_scouts(
    repop_and_factions: tuple[Any, Any],
) -> None:
    """Chief + shaman both down → kobold repop freezes and orc_vol scouts move in."""
    from evennia.utils import create  # noqa: PLC0415

    repop, factions = repop_and_factions
    chief, shaman = _kobold_leaders()
    baseline_tension = factions.get_tension("kobold", "orc_vol")
    room = create.create_object("typeclasses.rooms.Room", key="caves-halt-room-2")
    try:
        chief_mob = _make_leader_mob(chief.spawn_id, "Sharptooth", room)
        shaman_mob = _make_leader_mob(shaman.spawn_id, "Grik", room)

        chief_mob.at_death()
        shaman_mob.at_death()

        # The tribe is frozen (repop.md §3).
        halted_until = (repop.db.halted_until or {}).get("kobold")
        assert halted_until is not None and halted_until > time.time()

        # The designated rival (orc_vol) sends a scouting party (repop.md §4).
        scouts = repop.db.scouts or {}
        assert len(scouts) == repop_cfg.SCOUT_PARTY_SIZE
        assert all(s["faction"] == "orc_vol" for s in scouts.values())
        assert all(s["scouting"] == "kobold" for s in scouts.values())

        # The halt applies the R2 leadership_broken tension spike with the rival.
        assert factions.get_tension("kobold", "orc_vol") > baseline_tension
    finally:
        room.delete()


# ---------------------------------------------------------------------------
# Engine tests — faction standing shifts are observable in kobold behavior
# (faction.md §2.1, §5; the M4↔M9 tie this task delivers)
# ---------------------------------------------------------------------------


def _teardown_room(room: Any, *characters: Any) -> None:
    """Delete a room's remaining contents, the room, then any out-of-room chars.

    Mob.at_death leaves the base mob in place, so the room still holds it; clear
    contents first to avoid Evennia relocating soon-to-be-deleted objects to a
    deleted home during room.delete().
    """
    for obj in list(room.contents):
        if obj.pk is not None:
            obj.delete()
    room.delete()
    for char in characters:
        if char.pk is not None:
            char.delete()


def _make_kobold_mob(room: Any, key: str = "kobold-grunt", *, is_leader: bool = False) -> Any:
    from evennia.utils import create  # noqa: PLC0415

    mob = create.create_object("typeclasses.npcs.Mob", key=key, location=room)
    mob.db.faction_id = "kobold"
    mob.db.is_leader = is_leader
    return mob


@pytest.mark.django_db
def test_killing_kobold_member_lowers_player_standing(
    repop_and_factions: tuple[Any, Any],
) -> None:
    """Slaying a rank-and-file kobold drops the killer's kobold standing by 3."""
    from world.factions.config import STANDING_EVENTS  # noqa: PLC0415

    _, factions = repop_and_factions
    from evennia.utils import create  # noqa: PLC0415

    room = create.create_object("typeclasses.rooms.Room", key="caves-standing-room-1")
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="kobold-slayer-1")
    try:
        assert factions.get_standing("kobold", str(char.id)) == 0
        mob = _make_kobold_mob(room)
        mob.db.last_attacker = char
        mob.at_death()
        assert factions.get_standing("kobold", str(char.id)) == STANDING_EVENTS["kill_member"]
    finally:
        _teardown_room(room, char)


@pytest.mark.django_db
def test_killing_kobold_leader_lowers_standing_more(
    repop_and_factions: tuple[Any, Any],
) -> None:
    """A chief/shaman counts extra: standing drops by the larger kill_leader hit."""
    from world.factions.config import STANDING_EVENTS  # noqa: PLC0415

    _, factions = repop_and_factions
    from evennia.utils import create  # noqa: PLC0415

    room = create.create_object("typeclasses.rooms.Room", key="caves-standing-room-2")
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="kobold-slayer-2")
    try:
        chief = _make_kobold_mob(room, key="Sharptooth", is_leader=True)
        chief.db.last_attacker = char
        chief.at_death()
        assert factions.get_standing("kobold", str(char.id)) == STANDING_EVENTS["kill_leader"]
    finally:
        _teardown_room(room, char)


@pytest.mark.django_db
def test_unattributed_kobold_death_does_not_shift_standing(
    repop_and_factions: tuple[Any, Any],
) -> None:
    """A kobold dying with no recorded attacker credits no one (faction.md §2.1)."""
    _, factions = repop_and_factions
    from evennia.utils import create  # noqa: PLC0415

    room = create.create_object("typeclasses.rooms.Room", key="caves-standing-room-3")
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="kobold-bystander")
    try:
        mob = _make_kobold_mob(room)  # last_attacker left None
        mob.at_death()
        assert factions.get_standing("kobold", str(char.id)) == 0
    finally:
        _teardown_room(room, char)


@pytest.mark.django_db
def test_attack_command_records_last_attacker() -> None:
    """The attack command stamps the aggressor so a death can credit the kill."""
    from evennia.utils import create  # noqa: PLC0415

    from commands.combat import CmdAttack  # noqa: PLC0415

    room = create.create_object("typeclasses.rooms.Room", key="caves-attack-room")
    char = create.create_object(
        "typeclasses.characters.PlayerCharacter", key="kobold-fighter", location=room
    )
    mob = _make_kobold_mob(room)
    try:
        cmd = CmdAttack()
        cmd.caller = char
        cmd.args = f" {mob.key}"
        cmd.parse()
        cmd.func()
        assert mob.db.last_attacker is char
    finally:
        _teardown_room(room, char)


@pytest.mark.django_db
def test_henchman_kill_credits_employer(repop_and_factions: tuple[Any, Any]) -> None:
    """When a hired henchman lands the kill, the standing shift falls on its employer."""
    from world.factions.config import STANDING_EVENTS  # noqa: PLC0415

    _, factions = repop_and_factions
    from evennia.utils import create  # noqa: PLC0415

    room = create.create_object("typeclasses.rooms.Room", key="caves-henchman-room")
    employer = create.create_object("typeclasses.characters.PlayerCharacter", key="kobold-employer")
    henchman = create.create_object("typeclasses.npcs.Henchman", key="hired-blade", location=room)
    henchman.db.employer = employer
    try:
        mob = _make_kobold_mob(room)
        mob.db.last_attacker = henchman
        mob.at_death()
        assert factions.get_standing("kobold", str(employer.id)) == STANDING_EVENTS["kill_member"]
    finally:
        _teardown_room(room, employer)


@pytest.mark.django_db
def test_kobold_kills_drive_standing_to_kos_and_surviving_kobold_aggros(
    repop_and_factions: tuple[Any, Any],
) -> None:
    """End-to-end M4↔M9 tie: enough kobold kills turn the tribe kill-on-sight.

    Slaying ten kobolds drops the killer to kill-on-sight; a fresh kobold then
    attacks the moment the player enters its room (faction.md §2.1 → §5).
    """
    _, factions = repop_and_factions
    from evennia.utils import create  # noqa: PLC0415

    room = create.create_object("typeclasses.rooms.Room", key="caves-kos-room")
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="kobold-scourge")
    try:
        for i in range(10):
            mob = _make_kobold_mob(room, key=f"kobold-grunt-{i}")
            mob.db.last_attacker = char
            mob.at_death()
        assert factions.standing_band("kobold", str(char.id)) == "kill-on-sight"

        _make_kobold_mob(room, key="kobold-sentry-survivor")
        messages: list[str] = []
        char.msg = lambda text, **_kw: messages.append(str(text))
        char.move_to(room, quiet=True)
        assert any("attacks" in m.lower() for m in messages)
    finally:
        _teardown_room(room, char)


# ---------------------------------------------------------------------------
# Group 6 — Tribe discovery (fanout-harness.md §3; pure, no Evennia)
# ---------------------------------------------------------------------------


def test_discovery_finds_kobold_tribe() -> None:
    names = [m.__name__.rsplit(".", 1)[-1] for m in discovery.tribes()]
    assert "kobold" in names
    assert all(hasattr(m, "build") for m in discovery.tribes())


def test_discovery_skips_private_and_dunder() -> None:
    names = [m.__name__.rsplit(".", 1)[-1] for m in discovery.tribes()]
    assert not any(n.startswith("_") for n in names)
    assert "__pycache__" not in names
