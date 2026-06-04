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
from functools import cache

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


@cache
def _registry() -> dict[str, MobRecord]:
    """Return the memoised global template map, aggregating it on first use.

    The zone ``MOB_TEMPLATES`` are static module data, so re-scanning every zone
    per spawn point (``build_all`` resolves one template per spawn) is wasted work;
    aggregation runs once. The duplicate-key integrity check still fires (on that
    first build), and ``all_templates`` hands back a *copy* so a caller mutating the
    returned map never corrupts this shared cache.
    """
    return _aggregate(_ZONE_TEMPLATES)


def all_templates() -> dict[str, MobRecord]:
    """Return a copy of the global ``template_key -> MobRecord`` map across every zone."""
    return dict(_registry())


def get_template(key: str) -> MobRecord:
    """Return the ``MobRecord`` for ``key``; raise ``KeyError`` if unknown."""
    registry = _registry()
    if key not in registry:
        raise KeyError(f"unknown mob template {key!r}")
    return registry[key]
