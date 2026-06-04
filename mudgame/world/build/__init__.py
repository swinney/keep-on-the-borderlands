"""Runtime world-build / boot orchestrator package (world-build spec §3).

The Evennia-coupled layer that materialises the static zone content into a live,
populated world: the boot orchestrator (``orchestrator.build_all``), the mob
spawner (``spawner``), and the world-event deed hooks (``events``). Those modules
import Evennia lazily so importing the package stays Django-free.

Slice 1 (this commit) ships only ``templates`` — the pure ``template_key ->
MobRecord`` registry the spawner will read; the orchestrator/spawner/events
re-exports land in later slices (spec §14).

Slice 3 adds ``orchestrator.build_all()`` — the boot entry point — and
re-exports it here for the documented package interface (``rebuild_world`` lands
in slice 6). Importing ``orchestrator`` stays Django-free: it imports Evennia
lazily inside its functions.
"""

from __future__ import annotations

from world.build.orchestrator import build_all

__all__ = ["build_all"]
