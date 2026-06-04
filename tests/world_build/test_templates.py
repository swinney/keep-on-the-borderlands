"""Pure tests for the mob-template registry (world-build spec §5, §13.1).

Django-free: the registry aggregates the zone packages' pure ``MOB_TEMPLATES``
data, so it validates without booting Evennia (mirrors the pure zone tests).
"""

from __future__ import annotations

import pytest

from world.build import templates
from world.zones import caves, keep, shrine, wilderness
from world.zones.records import MobRecord


def _mob(key: str, faction: str = "kobold") -> MobRecord:
    """A minimal valid MobRecord for aggregation tests."""
    return MobRecord(
        key=key,
        name=key.replace("_", " ").title(),
        faction=faction,
        level=1,
        hd="1d8",
        ac=12,
        attacks="1d6",
        morale=7,
    )


def test_all_templates_aggregates_every_zone() -> None:
    """The registry covers Keep + Wilderness + every cave tribe + Shrine."""
    registry = templates.all_templates()
    expected: dict[str, MobRecord] = {}
    for zone_templates in (
        keep.MOB_TEMPLATES,
        wilderness.MOB_TEMPLATES,
        caves.MOB_TEMPLATES,
        shrine.MOB_TEMPLATES,
    ):
        for record in zone_templates:
            expected[record["key"]] = record
    assert registry == expected


def test_no_duplicate_keys_across_zones() -> None:
    """Template keys are globally unique — the count proves no key was clobbered."""
    total = sum(
        len(z)
        for z in (
            keep.MOB_TEMPLATES,
            wilderness.MOB_TEMPLATES,
            caves.MOB_TEMPLATES,
            shrine.MOB_TEMPLATES,
        )
    )
    assert len(templates.all_templates()) == total


def test_get_template_returns_record() -> None:
    """A known key resolves to its full stat block."""
    record = templates.get_template("kobold_chief")
    assert record["key"] == "kobold_chief"
    assert record["faction"] == "kobold"
    assert record.get("is_leader") is True


def test_get_template_unknown_key_raises_keyerror() -> None:
    """An unknown key raises KeyError, matching spawn_registry integrity."""
    with pytest.raises(KeyError, match="unknown mob template"):
        templates.get_template("no_such_mob")


def test_aggregate_rejects_duplicate_key() -> None:
    """Two sources sharing a key is a build-time integrity error."""
    dup = _mob("dup_mob")
    with pytest.raises(KeyError, match="duplicate mob template key"):
        templates._aggregate([[dup], [_mob("dup_mob", faction="orc")]])


def test_aggregate_merges_distinct_sources() -> None:
    """Distinct keys from several sources merge into one map."""
    merged = templates._aggregate([[_mob("a")], [_mob("b"), _mob("c")]])
    assert set(merged) == {"a", "b", "c"}
