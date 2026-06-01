"""Discover cave-tribe subpackages by filesystem enumeration."""

from __future__ import annotations

import importlib
import pkgutil
from types import ModuleType


def tribes() -> list[ModuleType]:
    import world.zones.caves as _caves_pkg  # noqa: PLC0415 (local: avoid circular import)

    found: list[ModuleType] = []
    for info in pkgutil.iter_modules(_caves_pkg.__path__):
        if not info.ispkg or info.name.startswith("_"):
            continue
        try:
            found.append(importlib.import_module(f"world.zones.caves.{info.name}"))
        except ImportError as e:
            raise ImportError(f"failed to load cave tribe subpackage 'caves.{info.name}'") from e
    return sorted(found, key=lambda m: m.__name__)
