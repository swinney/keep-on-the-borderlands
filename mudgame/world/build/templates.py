"""Pure mob-template registry (world-build spec §5, §13.1).

Aggregates every zone's ``MOB_TEMPLATES`` into a single
``template_key -> MobRecord`` map so the spawner can resolve a full stat block
from a ``SpawnPoint``'s template key alone. Pure — no Evennia import — mirroring
``world.zones.spawn_registry``: importing the zone packages stays Evennia-free
because each zone's ``build`` defers its Evennia import until called.

**Invariant:** template keys are globally unique across zones. The ``spawn_id``
namespace ``<zone>:<room>:<template>:<n>`` depends on it, so aggregation raises
``KeyError`` on a duplicate key — a build-time integrity error surfaced by a test
in ``tests/world_build/`` (the same integrity ``spawn_registry`` enforces on
spawn → template references).
"""

from __future__ import annotations

from collections.abc import Iterable

from world.zones import caves, keep, shrine, wilderness
from world.zones.records import MobRecord

# Each top-level zone package re-exports a pure ``MOB_TEMPLATES`` list. ``caves``
# already aggregates the ravine hub plus every discovered cave tribe, so these
# four lists are the whole game's mob-template corpus.
_ZONE_TEMPLATES: tuple[list[MobRecord], ...] = (
    keep.MOB_TEMPLATES,
    wilderness.MOB_TEMPLATES,
    caves.MOB_TEMPLATES,
    shrine.MOB_TEMPLATES,
)


def _aggregate(sources: Iterable[list[MobRecord]]) -> dict[str, MobRecord]:
    """Merge mob-template lists into a key→record map, rejecting duplicates."""
    registry: dict[str, MobRecord] = {}
    for templates in sources:
        for record in templates:
            key = record["key"]
            if key in registry:
                raise KeyError(f"duplicate mob template key {key!r}")
            registry[key] = record
    return registry


def all_templates() -> dict[str, MobRecord]:
    """Return the global ``template_key -> MobRecord`` map across every zone."""
    return _aggregate(_ZONE_TEMPLATES)


def get_template(key: str) -> MobRecord:
    """Return the ``MobRecord`` for ``key``; raise ``KeyError`` if unknown."""
    registry = all_templates()
    if key not in registry:
        raise KeyError(f"unknown mob template {key!r}")
    return registry[key]
