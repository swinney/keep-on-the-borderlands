"""Gnoll lair tests — Cave G (Hrrl's gnolls + the Owlbear).

Derived from docs/specs/zones/caves.md §Cave G and the fanout-harness.md §6
task template.  Pure-data groups validate static room/exit/mob/spawn data without
booting Evennia; engine groups (pytest-django) verify build() and the M4↔zone
faction/repop wiring.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from typing import Any

import pytest

from world.factions.config import FACTIONS, INITIAL_RELATIONS, RELATION_LADDER, band_for
from world.repop import config as repop_cfg
from world.zones import caves
from world.zones.caves import discovery, gnoll
from world.zones.spawn_registry import spawn_points

GNOLL_ROOMS: frozenset[str] = frozenset(
    {
        "gnoll_mouth",
        "gnoll_entry",
        "gnoll_raider_hall",
        "gnoll_hyena_pit",
        "gnoll_shaman",
        "gnoll_chief",
        "gnoll_owlbear_den",
    }
)


# ---------------------------------------------------------------------------
# Group 1 — Standard tribe interface (pure)
# ---------------------------------------------------------------------------


def test_gnoll_package_exposes_standard_interface() -> None:
    assert callable(gnoll.build)
    assert isinstance(gnoll.ROOMS, list)
    assert isinstance(gnoll.EXITS, list)
    assert isinstance(gnoll.MOB_TEMPLATES, list)
    assert isinstance(gnoll.SPAWNS, list)
    assert isinstance(gnoll.NPCS, list)


def test_discovery_finds_gnoll_tribe() -> None:
    names = [m.__name__.rsplit(".", 1)[-1] for m in discovery.tribes()]
    assert "gnoll" in names


# ---------------------------------------------------------------------------
# Group 2 — Room / exit data integrity (pure)
# ---------------------------------------------------------------------------


def test_gnoll_room_keys_unique() -> None:
    keys = [r["key"] for r in gnoll.ROOMS]
    assert len(keys) == len(set(keys)), "duplicate room key in gnoll ROOMS"


def test_expected_gnoll_rooms_present() -> None:
    keys = {r["key"] for r in gnoll.ROOMS}
    assert keys >= GNOLL_ROOMS, f"missing gnoll rooms: {GNOLL_ROOMS - keys}"


def test_gnoll_has_exactly_seven_rooms() -> None:
    assert len(gnoll.ROOMS) == 7, "Cave G spec requires exactly 7 rooms"


def test_gnoll_lair_rooms_are_dark() -> None:
    by_key = {r["key"]: r for r in gnoll.ROOMS}
    for key in GNOLL_ROOMS:
        assert by_key[key].get("dark") is True, f"{key} should be dark"


def test_no_dangling_gnoll_intra_zone_exits() -> None:
    all_rooms = {r["key"] for r in caves.ROOMS}
    for exit_ in gnoll.EXITS:
        src = exit_["from"]
        dst = exit_["to"]
        if ":" in dst:
            continue
        assert src in all_rooms, f"exit from unknown room {src!r}"
        assert dst in all_rooms, f"exit to unknown room {dst!r}"


def test_ravine_south_connects_to_gnoll_mouth() -> None:
    """Gnoll entrance attaches south to the southern ledges (caves spec §ravine)."""
    from_south = {e["to"] for e in gnoll.EXITS if e["from"] == "ravine_south"}
    assert "gnoll_mouth" in from_south, "gnoll cave mouth not off ravine_south"


def test_gnoll_entrance_is_south_from_ravine_south() -> None:
    """Cave G uses the south exit from ravine_south."""
    south_exits = [e for e in gnoll.EXITS if e["from"] == "ravine_south" and e["dir"] == "s"]
    assert south_exits, "no south exit from ravine_south to gnoll lair"
    assert south_exits[0]["to"] == "gnoll_mouth"


def test_gnoll_exits_are_bidirectional() -> None:
    """Each link must appear in both directions (expand produces both)."""
    pairs: set[tuple[str, str]] = set()
    for e in gnoll.EXITS:
        pairs.add((e["from"], e["to"]))
    for src, dst in list(pairs):
        assert (dst, src) in pairs, f"exit {src!r} -> {dst!r} has no return"


# ---------------------------------------------------------------------------
# Group 3 — Mob templates (pure)
# ---------------------------------------------------------------------------


def test_gnoll_mob_keys_unique() -> None:
    keys = [m["key"] for m in gnoll.MOB_TEMPLATES]
    assert len(keys) == len(set(keys))


def test_gnoll_tribe_mobs_use_gnoll_faction() -> None:
    gnoll_mobs = [m for m in gnoll.MOB_TEMPLATES if m["faction"] == "gnoll"]
    assert gnoll_mobs, "no gnoll faction mobs defined"
    keys = {m["key"] for m in gnoll_mobs}
    assert "gnoll_raider" in keys
    assert "gnoll_chief" in keys
    assert "gnoll_shaman" in keys


def test_owlbear_uses_owlbear_faction() -> None:
    owlbear_mobs = [m for m in gnoll.MOB_TEMPLATES if m["faction"] == "owlbear"]
    assert owlbear_mobs, "no owlbear faction mob defined in gnoll package"
    keys = {m["key"] for m in owlbear_mobs}
    assert "cave_g_owlbear" in keys


def test_gnoll_mob_factions_are_valid_ids() -> None:
    valid = set(FACTIONS.keys())
    for mob in gnoll.MOB_TEMPLATES:
        assert mob["faction"] in valid, f"mob {mob['key']!r} bad faction {mob['faction']!r}"


def test_gnoll_mob_ascending_ac_in_range() -> None:
    for mob in gnoll.MOB_TEMPLATES:
        assert mob["ac"] >= 10, f"mob {mob['key']!r} AC {mob['ac']} below ascending base 10"


def test_hrrl_is_chief_leader() -> None:
    hrrl = next((m for m in gnoll.MOB_TEMPLATES if m["key"] == "gnoll_chief"), None)
    assert hrrl is not None
    assert hrrl.get("is_leader") is True
    assert hrrl.get("leader_role") == "chief"


def test_mange_is_shaman_leader() -> None:
    mange = next((m for m in gnoll.MOB_TEMPLATES if m["key"] == "gnoll_shaman"), None)
    assert mange is not None
    assert mange.get("is_leader") is True
    assert mange.get("leader_role") == "shaman"


# ---------------------------------------------------------------------------
# Group 4 — Spawns + leadership (pure)
# ---------------------------------------------------------------------------


def test_gnoll_spawn_templates_defined() -> None:
    mob_keys = {m["key"] for m in gnoll.MOB_TEMPLATES}
    for spawn in gnoll.SPAWNS:
        assert spawn["template"] in mob_keys, (
            f"spawn in {spawn['room']!r} references unknown template {spawn['template']!r}"
        )


def test_gnoll_spawn_rooms_exist() -> None:
    all_room_keys = {r["key"] for r in caves.ROOMS}
    for spawn in gnoll.SPAWNS:
        assert spawn["room"] in all_room_keys, f"spawn references unknown room {spawn['room']!r}"


def test_gnoll_tribe_has_exactly_one_chief_and_one_shaman() -> None:
    leader_spawns = [
        s for s in gnoll.SPAWNS if s.get("is_leader") and s["room"].startswith("gnoll")
    ]
    roles = [s.get("leader_role") for s in leader_spawns]
    assert roles.count("chief") == 1, "gnoll needs exactly one chief spawn"
    assert roles.count("shaman") == 1, "gnoll needs exactly one shaman spawn"


def test_gnoll_leader_spawns_are_single() -> None:
    for spawn in gnoll.SPAWNS:
        if spawn.get("is_leader"):
            assert spawn.get("leader_role") in {"chief", "shaman"}
            assert spawn["count"] == 1, "a leader spawn must be count=1"


def test_hrrl_spawn_is_in_chief_hall() -> None:
    hrrl_spawns = [s for s in gnoll.SPAWNS if s["template"] == "gnoll_chief"]
    assert hrrl_spawns, "gnoll_chief spawn must be defined"
    assert hrrl_spawns[0]["room"] == "gnoll_chief"


def test_mange_spawn_is_in_shaman_den() -> None:
    mange_spawns = [s for s in gnoll.SPAWNS if s["template"] == "gnoll_shaman"]
    assert mange_spawns, "gnoll_shaman spawn must be defined"
    assert mange_spawns[0]["room"] == "gnoll_shaman"


def test_owlbear_spawn_is_not_a_leader() -> None:
    """The owlbear is a beast, not a gnoll tribal leader."""
    owlbear_spawns = [s for s in gnoll.SPAWNS if s["template"] == "cave_g_owlbear"]
    assert owlbear_spawns, "cave_g_owlbear spawn must be defined"
    for spawn in owlbear_spawns:
        assert not spawn.get("is_leader"), "the owlbear must not be a gnoll leader"


# ---------------------------------------------------------------------------
# Group 5 — War rivalry + owlbear beast config (pure)
# ---------------------------------------------------------------------------


def test_gnoll_goblin_initial_tension_is_war() -> None:
    """The faction config encodes the gnoll↔goblin feud at war-band tension (+20)."""
    pair = frozenset({"gnoll", "goblin"})
    tension = INITIAL_RELATIONS[pair]
    assert band_for(tension, RELATION_LADDER) == "war"


def test_gnoll_designated_rival_is_goblin() -> None:
    assert repop_cfg.DESIGNATED_RIVAL["gnoll"] == "goblin"


def test_goblin_designated_rival_is_gnoll() -> None:
    assert repop_cfg.DESIGNATED_RIVAL["goblin"] == "gnoll"


# ---------------------------------------------------------------------------
# Group 6 — Spawn-point derivation (pure, no Evennia)
# ---------------------------------------------------------------------------


def test_gnoll_spawn_points_expand_count() -> None:
    points = spawn_points("caves", gnoll.SPAWNS, gnoll.MOB_TEMPLATES)
    assert len(points) == sum(s["count"] for s in gnoll.SPAWNS)


def test_gnoll_spawn_point_ids_unique() -> None:
    points = spawn_points("caves", gnoll.SPAWNS, gnoll.MOB_TEMPLATES)
    ids = [p.spawn_id for p in points]
    assert len(ids) == len(set(ids))


def test_gnoll_derived_leaders() -> None:
    points = spawn_points("caves", gnoll.SPAWNS, gnoll.MOB_TEMPLATES)
    gnoll_leaders = [p for p in points if p.is_leader and p.faction == "gnoll"]
    roles = [p.leader_role for p in gnoll_leaders]
    assert roles.count("chief") == 1
    assert roles.count("shaman") == 1


def test_owlbear_spawn_point_has_owlbear_faction() -> None:
    points = spawn_points("caves", gnoll.SPAWNS, gnoll.MOB_TEMPLATES)
    owlbear_points = [p for p in points if p.mob_template == "cave_g_owlbear"]
    assert owlbear_points, "cave_g_owlbear spawn point must exist"
    assert all(p.faction == "owlbear" for p in owlbear_points)
    assert all(not p.is_leader for p in owlbear_points)


def test_gnoll_spawn_point_rooms_are_zone_namespaced() -> None:
    for point in spawn_points("caves", gnoll.SPAWNS, gnoll.MOB_TEMPLATES):
        assert point.room.startswith("caves:")


# ---------------------------------------------------------------------------
# Engine fixtures
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
    """Build the caves zone (hub + all discovered tribes), yield, tear down."""
    caves.build()
    try:
        yield
    finally:
        for exit_ in _caves_exits():
            exit_.delete()
        for room in _caves_rooms():
            room.delete()


@pytest.fixture
def repop_and_factions() -> Iterator[tuple[Any, Any]]:
    """A registered repop_manager + faction_manager, torn down after the test."""
    from evennia.utils import create  # noqa: PLC0415

    all_spawns = caves.SPAWNS
    all_mobs = caves.MOB_TEMPLATES
    repop = create.create_script("world.managers.repop_manager.RepopManager")
    factions = create.create_script("world.managers.faction_manager.FactionManager")
    repop.register_zone("caves", all_spawns, all_mobs)
    try:
        yield repop, factions
    finally:
        repop.delete()
        factions.delete()


# ---------------------------------------------------------------------------
# Engine tests — build() materialises the gnoll lair
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_build_creates_gnoll_rooms(built_caves: None) -> None:
    built = {r.db.room_key for r in _caves_rooms()}
    assert built >= GNOLL_ROOMS, f"missing: {GNOLL_ROOMS - built}"


@pytest.mark.django_db
def test_gnoll_lair_rooms_have_dark_flag(built_caves: None) -> None:
    from world.zones.builder import FLAG_CATEGORY  # noqa: PLC0415

    chief = _find_caves_room("gnoll_chief")
    assert chief is not None
    assert chief.tags.has("dark", category=FLAG_CATEGORY)


@pytest.mark.django_db
def test_owlbear_den_has_dark_flag(built_caves: None) -> None:
    from world.zones.builder import FLAG_CATEGORY  # noqa: PLC0415

    den = _find_caves_room("gnoll_owlbear_den")
    assert den is not None
    assert den.tags.has("dark", category=FLAG_CATEGORY)


@pytest.mark.django_db
def test_ravine_south_exits_to_gnoll_mouth(built_caves: None) -> None:
    ravine_south = _find_caves_room("ravine_south")
    assert ravine_south is not None
    dest_keys = {e.destination.db.room_key for e in ravine_south.exits if e.destination}
    assert "gnoll_mouth" in dest_keys, "ravine_south has no exit into gnoll lair"


@pytest.mark.django_db
def test_gnoll_internal_exits_are_reversible(built_caves: None) -> None:
    mouth = _find_caves_room("gnoll_mouth")
    entry = _find_caves_room("gnoll_entry")
    assert mouth is not None and entry is not None
    north = [e for e in mouth.exits if e.key == "n"]
    assert north and north[0].destination == entry
    south = [e for e in entry.exits if e.key == "s"]
    assert south and south[0].destination == mouth


@pytest.mark.django_db
def test_chief_hall_accessible_from_raider_hall(built_caves: None) -> None:
    hall = _find_caves_room("gnoll_raider_hall")
    chief = _find_caves_room("gnoll_chief")
    assert hall is not None and chief is not None
    north = [e for e in hall.exits if e.key == "n"]
    assert north and north[0].destination == chief


@pytest.mark.django_db
def test_owlbear_den_accessible_from_chief_hall(built_caves: None) -> None:
    chief = _find_caves_room("gnoll_chief")
    den = _find_caves_room("gnoll_owlbear_den")
    assert chief is not None and den is not None
    west = [e for e in chief.exits if e.key == "w"]
    assert west and west[0].destination == den


# ---------------------------------------------------------------------------
# Engine tests — gnoll leadership halt + goblin rival scouting
# ---------------------------------------------------------------------------


def _gnoll_leaders() -> tuple[Any, Any]:
    points = spawn_points("caves", caves.SPAWNS, caves.MOB_TEMPLATES)
    chief = next(p for p in points if p.leader_role == "chief" and p.faction == "gnoll")
    shaman = next(p for p in points if p.leader_role == "shaman" and p.faction == "gnoll")
    return chief, shaman


def _make_leader_mob(spawn_id: str, key: str, faction: str, room: Any) -> Any:
    from evennia.utils import create  # noqa: PLC0415

    mob = create.create_object("typeclasses.npcs.Mob", key=key, location=room)
    mob.db.spawn_id = spawn_id
    mob.db.faction_id = faction
    return mob


@pytest.mark.django_db
def test_killing_one_gnoll_leader_does_not_halt(
    repop_and_factions: tuple[Any, Any],
) -> None:
    from evennia.utils import create  # noqa: PLC0415

    repop, _ = repop_and_factions
    chief, _shaman = _gnoll_leaders()
    room = create.create_object("typeclasses.rooms.Room", key="gnoll-halt-room-1")
    try:
        chief_mob = _make_leader_mob(chief.spawn_id, "Hrrl", "gnoll", room)
        chief_mob.at_death()
        assert chief.spawn_id in (repop.db.respawn_at or {})
        assert "gnoll" not in (repop.db.halted_until or {})
        assert not (repop.db.scouts or {})
    finally:
        room.delete()


@pytest.mark.django_db
def test_killing_both_gnoll_leaders_halts_and_goblin_scouts(
    repop_and_factions: tuple[Any, Any],
) -> None:
    """Gnoll chief + shaman down → tribe frozen, goblins scout the lair."""
    from evennia.utils import create  # noqa: PLC0415

    repop, factions = repop_and_factions
    chief, shaman = _gnoll_leaders()
    baseline = factions.get_tension("gnoll", "goblin")
    room = create.create_object("typeclasses.rooms.Room", key="gnoll-halt-room-2")
    try:
        chief_mob = _make_leader_mob(chief.spawn_id, "Hrrl", "gnoll", room)
        shaman_mob = _make_leader_mob(shaman.spawn_id, "Mange", "gnoll", room)
        chief_mob.at_death()
        shaman_mob.at_death()

        halted_until = (repop.db.halted_until or {}).get("gnoll")
        assert halted_until is not None and halted_until > time.time()

        scouts = repop.db.scouts or {}
        assert len(scouts) == repop_cfg.SCOUT_PARTY_SIZE
        assert all(s["faction"] == "goblin" for s in scouts.values())
        assert all(s["scouting"] == "gnoll" for s in scouts.values())

        assert factions.get_tension("gnoll", "goblin") > baseline
    finally:
        room.delete()


# ---------------------------------------------------------------------------
# Engine tests — faction standing shifts observable in gnoll behavior
# ---------------------------------------------------------------------------


def _teardown_room(room: Any, *characters: Any) -> None:
    for obj in list(room.contents):
        if obj.pk is not None:
            obj.delete()
    room.delete()
    for char in characters:
        if char.pk is not None:
            char.delete()


def _make_gnoll_mob(
    room: Any,
    faction: str = "gnoll",
    key: str = "gnoll-grunt",
    *,
    is_leader: bool = False,
) -> Any:
    from evennia.utils import create  # noqa: PLC0415

    mob = create.create_object("typeclasses.npcs.Mob", key=key, location=room)
    mob.db.faction_id = faction
    mob.db.is_leader = is_leader
    return mob


@pytest.mark.django_db
def test_killing_gnoll_member_lowers_player_standing(
    repop_and_factions: tuple[Any, Any],
) -> None:
    from world.factions.config import STANDING_EVENTS  # noqa: PLC0415

    _, factions = repop_and_factions
    from evennia.utils import create  # noqa: PLC0415

    room = create.create_object("typeclasses.rooms.Room", key="gnoll-standing-room-1")
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="gnoll-slayer")
    try:
        assert factions.get_standing("gnoll", str(char.id)) == 0
        mob = _make_gnoll_mob(room)
        mob.db.last_attacker = char
        mob.at_death()
        assert factions.get_standing("gnoll", str(char.id)) == STANDING_EVENTS["kill_member"]
    finally:
        _teardown_room(room, char)


@pytest.mark.django_db
def test_killing_gnoll_leader_lowers_standing_more(
    repop_and_factions: tuple[Any, Any],
) -> None:
    from world.factions.config import STANDING_EVENTS  # noqa: PLC0415

    _, factions = repop_and_factions
    from evennia.utils import create  # noqa: PLC0415

    room = create.create_object("typeclasses.rooms.Room", key="gnoll-standing-room-2")
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="gnoll-leader-slayer")
    try:
        hrrl = _make_gnoll_mob(room, key="Hrrl", is_leader=True)
        hrrl.db.last_attacker = char
        hrrl.at_death()
        assert factions.get_standing("gnoll", str(char.id)) == STANDING_EVENTS["kill_leader"]
    finally:
        _teardown_room(room, char)


@pytest.mark.django_db
def test_killing_owlbear_shifts_owlbear_standing_not_gnoll(
    repop_and_factions: tuple[Any, Any],
) -> None:
    """Killing the owlbear affects `owlbear` faction standing, not `gnoll`."""
    from world.factions.config import STANDING_EVENTS  # noqa: PLC0415

    _, factions = repop_and_factions
    from evennia.utils import create  # noqa: PLC0415

    room = create.create_object("typeclasses.rooms.Room", key="gnoll-owlbear-standing-room")
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="owlbear-slayer")
    try:
        owlbear = _make_gnoll_mob(room, faction="owlbear", key="the Owlbear")
        owlbear.db.last_attacker = char
        owlbear.at_death()
        assert factions.get_standing("owlbear", str(char.id)) == STANDING_EVENTS["kill_member"]
        assert factions.get_standing("gnoll", str(char.id)) == 0
    finally:
        _teardown_room(room, char)


@pytest.mark.django_db
def test_gnoll_kills_drive_to_kos_and_survivor_aggros(
    repop_and_factions: tuple[Any, Any],
) -> None:
    """End-to-end M4↔zone tie: enough gnoll kills → kill-on-sight; survivor aggros."""
    _, factions = repop_and_factions
    from evennia.utils import create  # noqa: PLC0415

    room = create.create_object("typeclasses.rooms.Room", key="gnoll-kos-room")
    char = create.create_object("typeclasses.characters.PlayerCharacter", key="gnoll-scourge")
    try:
        for i in range(10):
            mob = _make_gnoll_mob(room, key=f"gnoll-grunt-{i}")
            mob.db.last_attacker = char
            mob.at_death()
        assert factions.standing_band("gnoll", str(char.id)) == "kill-on-sight"

        _make_gnoll_mob(room, key="gnoll-sentry-survivor")
        messages: list[str] = []
        char.msg = lambda text, **_kw: messages.append(str(text))
        char.move_to(room, quiet=True)
        assert any("attacks" in m.lower() for m in messages)
    finally:
        _teardown_room(room, char)
