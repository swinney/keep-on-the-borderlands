"""Live mob spawner: a ``MobRecord`` template + a room → a live ``Mob`` (spec §6-§7).

Replaces the ``repop_manager``'s no-op ``_instantiate`` / ``_instantiate_scout`` /
``_retreat_scout`` (world-build spec §2). The ``repop_manager`` keeps owning
*when* to spawn (respawn timers, leadership-halt windows, the 24h Shrine cycle);
this module owns *how* — materialising a registered ``SpawnPoint`` (or a rival
``Scout``) into an Evennia ``Mob`` with OSE stats, faction, leader flag, and the
``spawn_id`` back-reference that makes the mob's death report home (repop.md §1).

Evennia is imported lazily inside each function so importing this module stays
Django-free — only the pure templates registry, the repop dataclasses, the pure
rules, and the record typing are import-time dependencies. This is the same
discipline every zone ``build.py`` follows, and it keeps the pure helpers
(``hd_notation``, ``roll_hp``) unit-testable without booting the server.

Instance identity (spec §7): each live spawned object carries a spawn-instance
tag — its ``spawn_id`` (mobs) or ``scout_id`` (scouts) — in the
``spawn_instance`` category. ``spawn_mob`` skips when a *live* instance already
exists, so the initial population pass and a repop tick converge to exactly one
live mob per due point; a *dead* instance is cleared first so the next respawn
re-creates it, and ``despawn`` removes the tag on retreat/reset.
"""

from __future__ import annotations

import random
import re
from typing import Any

from world.build import templates
from world.repop.state import Scout, SpawnPoint
from world.rules import dice
from world.rules.combat import is_dead
from world.zones.records import MobRecord

# Tag category marking a live spawned instance by its spawn_id / scout_id (§7).
SPAWN_INSTANCE_CATEGORY = "spawn_instance"

MOB_TYPECLASS = "typeclasses.npcs.Mob"

# OSE hit dice without an explicit die are a count of d8 (a Hit Die is a d8),
# carrying an optional flat hit-point modifier ("2" → 2d8, "1+1" → 1d8+1).
_HD_COUNT = re.compile(r"(\d+)([+-]\d+)?")


# ── Pure helpers (Django-free; unit-tested directly) ─────────────────────────


def hd_notation(hd: str) -> str:
    """Translate an OSE hit-dice string into ``NdM(+K)`` dice notation (spec §6).

    OSE writes monster hit points as a Hit Die count of d8 with an optional flat
    modifier ("2" → ``"2d8"``, "1+1" → ``"1d8+1"``, "1-1" → ``"1d8-1"``); a value
    that already carries an explicit die ("1d4", for a sub-HD kobold) passes
    through unchanged. Raises ``ValueError`` on anything malformed, matching
    ``dice.parse``'s strictness.
    """
    text = "".join(hd.split())
    if "d" in text.lower():
        return text
    match = _HD_COUNT.fullmatch(text)
    if match is None:
        raise ValueError(f"malformed hit dice: {hd!r}")
    count, modifier = match.group(1), match.group(2) or ""
    return f"{count}d8{modifier}"


def roll_hp(record: MobRecord, rng: random.Random) -> int:
    """Roll a mob's starting hit points from its record (floor 1; spec §6).

    Threaded through the seeded-RNG seam (architecture §5.2) so a spawn's HP is
    deterministic under test. A Hit Die floored at 1 mirrors
    ``progression.roll_hit_points`` — even a "1-1" mob never spawns at 0 HP.
    """
    return max(1, dice.roll(hd_notation(record["hd"]), rng=rng))


def _scout_template(faction: str) -> MobRecord | None:
    """A representative non-leader template for a rival scout's faction (§6).

    A ``Scout`` names only its faction and room, so the spawner picks a rank-and-
    file template of that faction (the lowest key, deterministically; never a
    chief/shaman). Returns ``None`` when the faction has no templates at all.
    """
    registry = templates.all_templates()
    candidates = [
        r for r in registry.values() if r["faction"] == faction and not r.get("is_leader")
    ]
    if not candidates:
        candidates = [r for r in registry.values() if r["faction"] == faction]
    if not candidates:
        return None
    return min(candidates, key=lambda record: record["key"])


# ── Evennia materialisation (lazy imports; objects typed Any per builder idiom) ─


def _find_instance(instance_id: str) -> Any:
    """Return the live object tagged ``instance_id`` in ``spawn_instance``, or None."""
    from evennia.utils.search import search_object_by_tag  # noqa: PLC0415

    matches = search_object_by_tag(instance_id, category=SPAWN_INSTANCE_CATEGORY)
    return matches[0] if matches else None


def _find_room(room: str) -> Any:
    """Resolve the live room carrying the builder's ``"<zone>:<key>"`` tag, or None."""
    from evennia.utils.search import search_object_by_tag  # noqa: PLC0415

    from world.zones.builder import ROOM_CATEGORY  # noqa: PLC0415

    matches = search_object_by_tag(room, category=ROOM_CATEGORY)
    return matches[0] if matches else None


def _apply_record(mob: Any, record: MobRecord, rng: random.Random) -> None:
    """Set a freshly created mob's OSE traits from its template (spec §6).

    ``ac`` is ascending (architecture §5.1); ``level`` and ``morale`` come from
    the record; ``attack_bonus`` scales with the mob's level — OSE monsters throw
    to hit by Hit Dice, and the record's ``level`` carries that (players read
    theirs from the class table, combat.md §2; there is no separate monster table
    in ``world/rules``). HP is rolled through the seeded RNG and re-adds the gauge
    so ``current`` starts at the rolled maximum (mirroring ``TargetDummy``).
    """
    traits = mob.traits
    traits.ac.base = record["ac"]
    traits.level.base = record["level"]
    traits.morale.base = record["morale"]
    traits.attack_bonus.base = record["level"]
    traits.add("hp", "Hit Points", trait_type="gauge", base=roll_hp(record, rng), mod=0)


def spawn_mob(point: SpawnPoint, *, rng: random.Random | None = None) -> Any:
    """Materialise ``point``'s mob template into a live ``Mob`` (spec §6).

    Idempotent (§7): if a live instance of ``point.spawn_id`` already stands, it
    is returned unchanged; a dead one is cleared first so the respawn re-creates
    it. Returns ``None`` (logged, not raised) when the target room is not built
    yet — the deferred-room safety property (§13.3) that keeps a partial world
    from wedging the repop tick.
    """
    from evennia.utils import create, logger  # noqa: PLC0415

    existing = _find_instance(point.spawn_id)
    if existing is not None:
        if not _is_dead(existing):
            return existing
        existing.delete()

    room = _find_room(point.room)
    if room is None:
        logger.log_info(f"spawner: room {point.room!r} not built; skipping {point.spawn_id}")
        return None

    record = templates.get_template(point.mob_template)
    mob = create.create_object(MOB_TYPECLASS, key=record["name"], location=room)
    _apply_record(mob, record, rng if rng is not None else random.Random())
    mob.db.faction_id = record["faction"]
    mob.db.is_leader = point.is_leader
    mob.db.spawn_id = point.spawn_id
    mob.tags.add(point.spawn_id, category=SPAWN_INSTANCE_CATEGORY)
    return mob


def spawn_scout(scout: Scout, *, rng: random.Random | None = None) -> Any:
    """Materialise a rival ``scout`` in a broken tribe's lair room (spec §6).

    Picks a rank-and-file template of the scout's (rival) faction and tags the
    instance with ``scout_id`` — not ``spawn_id`` — so it despawns on retreat and
    its death credits the rival faction via ``notify_scout_death`` rather than the
    spawn-point respawn path. Idempotent and room-deferred like ``spawn_mob``;
    returns ``None`` when the room is unbuilt or the faction has no template.
    """
    from evennia.utils import create, logger  # noqa: PLC0415

    existing = _find_instance(scout.scout_id)
    if existing is not None:
        return existing

    room = _find_room(scout.room)
    if room is None:
        logger.log_info(f"spawner: room {scout.room!r} not built; skipping scout {scout.scout_id}")
        return None

    record = _scout_template(scout.faction)
    if record is None:
        logger.log_info(
            f"spawner: no template for faction {scout.faction!r}; scout {scout.scout_id} skipped"
        )
        return None

    mob = create.create_object(MOB_TYPECLASS, key=record["name"], location=room)
    _apply_record(mob, record, rng if rng is not None else random.Random())
    mob.db.faction_id = scout.faction
    mob.db.is_leader = False
    mob.db.scout_id = scout.scout_id
    mob.tags.add(scout.scout_id, category=SPAWN_INSTANCE_CATEGORY)
    return mob


def despawn(instance_id: str) -> bool:
    """Delete the live instance tagged ``instance_id``; return whether any existed.

    Used by ``_retreat_scout`` (a scout regroups out of a lair) and by any
    rebuild that must clear a stale instance before re-spawning (spec §6-§7).
    """
    from evennia.utils.search import search_object_by_tag  # noqa: PLC0415

    matches = search_object_by_tag(instance_id, category=SPAWN_INSTANCE_CATEGORY)
    for obj in matches:
        obj.delete()
    return bool(matches)


def _is_dead(mob: Any) -> bool:
    """True when a spawned mob instance is at 0 HP (combat.md §4.2)."""
    return is_dead(int(mob.traits.hp.value))
