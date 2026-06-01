"""Henchmen subsystem (docs/specs/henchmen.md)."""

from __future__ import annotations

from evennia.objects.models import ObjectDB


def reset_henchmen() -> None:
    """Delete all Henchman instances on season reset (henchmen.md §6).

    Henchmen are world NPCs and do not persist across seasons.
    Called by the season_manager (M6).
    """
    for record in list(ObjectDB.objects.filter(db_typeclass_path="typeclasses.npcs.Henchman")):
        record.delete()
