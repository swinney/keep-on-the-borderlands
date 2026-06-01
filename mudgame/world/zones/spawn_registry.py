"""Derive repop ``SpawnPoint``s from a zone's static spawn + mob data (R3 §1).

Pure — no Evennia import — so the derivation is unit-testable without booting
the server. The repop_manager wraps this (``register_zone``) to register a
zone's tribe spawns; killing both designated leaders of a tribe within one
window then fires the leadership halt and rival scouting (repop.md §3-4).

A ``SpawnRecord`` may stand for several individual mobs (``count`` > 1); each
becomes its own ``SpawnPoint`` with a stable, unique ``spawn_id`` so respawn is
per-mob (repop.md §2). The point's faction is read from the named mob template
(repop.md §1: "the mob template names its faction"); ``room`` is namespaced
``"<zone>:<room_key>"`` so the manager can resolve the live room by tag.
"""

from __future__ import annotations

from world.repop.state import SpawnPoint
from world.zones.records import MobRecord, SpawnRecord


def spawn_points(
    zone: str,
    spawns: list[SpawnRecord],
    mob_templates: list[MobRecord],
) -> list[SpawnPoint]:
    """Expand a zone's spawn records into per-mob ``SpawnPoint``s.

    Raises ``KeyError`` if a spawn names a template absent from ``mob_templates``
    (the same integrity the zone tests assert on the static data).
    """
    faction_by_template = {m["key"]: m["faction"] for m in mob_templates}
    # Running per-(room, template) index so split records never collide on id.
    seen: dict[tuple[str, str], int] = {}
    points: list[SpawnPoint] = []
    for spawn in spawns:
        template = spawn["template"]
        if template not in faction_by_template:
            raise KeyError(f"spawn references unknown mob template {template!r}")
        room_key = spawn["room"]
        for _ in range(spawn["count"]):
            index = seen.get((room_key, template), 0)
            seen[(room_key, template)] = index + 1
            points.append(
                SpawnPoint(
                    spawn_id=f"{zone}:{room_key}:{template}:{index}",
                    room=f"{zone}:{room_key}",
                    mob_template=template,
                    faction=faction_by_template[template],
                    respawn_seconds=spawn["respawn_seconds"],
                    is_leader=spawn.get("is_leader", False),
                    leader_role=spawn.get("leader_role"),
                )
            )
    return points
