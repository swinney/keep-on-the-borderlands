"""Keep static NPCs: the tavern roster host and the chapel staff.

This slice (M7) wires two of the Keep's living features:

* **Tavern roster integration.** The One-Eyed Cat's tavernkeeper anchors the
  henchmen hiring hall. The recruit roster itself is pure config
  (``world.henchmen.config.ROSTER``); the ``roster``/``hire`` commands
  (``commands.henchmen``) read it when the player stands in the ``tavern`` room.
* **Chapel staff (priest-pool placeholder).** The Curate plus the five-NPC pool
  the disguised-priest plot draws its seasonal spy from (disguised-priest.md
  §2). Here they are plain, peaceful ``ServiceNpc``s placed in the chapel rooms
  and tagged ``priest_pool`` by the builder; the ``priest_manager`` rotation,
  clue tells, and detection paths land later in M12.

Shop vendors (provisioner/armorer/weaponsmith/trader) and the bank are realised
as room-scoped commands (``commands.economy``) rather than NPC objects, so they
are intentionally absent from this list; quest-giver NPCs land with M9/M13.

The records follow the zones-spec ``NpcRecord`` shape (zones.md §1); ``PLACEMENT``
maps each NPC ``key`` to the Keep room it stands in (placement is build data,
kept out of the record shape so the record stays spec-faithful).
"""

from __future__ import annotations

from world.zones.records import NpcRecord

# Chapel staff the disguised-priest plot rotates its spy through
# (docs/specs/disguised-priest.md §2). The builder tags these NPCs so the
# M12 priest_manager can find the pool.
PRIEST_POOL: tuple[str, ...] = ("anselm", "maeve", "ortho", "bellan", "gisla")

NPCS: list[NpcRecord] = [
    {
        "key": "tavernkeeper",
        "name": "Hroth",
        "sdesc": "the one-eyed tavernkeeper",
        "role": "tavernkeeper",
    },
    {
        "key": "guildmaster",
        "name": "The Guildmaster",
        "sdesc": "the grizzled guildmaster of adventurers",
        "role": "guildmaster",
        "giver_key": "guildmaster",
    },
    {
        "key": "castellan",
        "name": "The Castellan",
        "sdesc": "the iron-willed Castellan of the Keep",
        "role": "castellan",
        "giver_key": "castellan",
    },
    {
        "key": "curate",
        "name": "The Curate",
        "sdesc": "the Keep's grey-robed Curate",
        "role": "curate",
        "giver_key": "curate",
    },
    {
        "key": "anselm",
        "name": "Anselm",
        "sdesc": "a soft-spoken friar",
        "role": "almoner",
    },
    {
        "key": "maeve",
        "name": "Maeve",
        "sdesc": "a stern sister",
        "role": "reliquary keeper",
    },
    {
        "key": "ortho",
        "name": "Ortho",
        "sdesc": "a portly deacon",
        "role": "deacon",
    },
    {
        "key": "bellan",
        "name": "Bellan",
        "sdesc": "a young bellringer",
        "role": "bellringer",
    },
    {
        "key": "gisla",
        "name": "Gisla",
        "sdesc": "a wandering pardoner",
        "role": "pardoner",
    },
]

# NPC key -> Keep room key (zones.md §1; Keep outline NPC table).
PLACEMENT: dict[str, str] = {
    "tavernkeeper": "tavern",
    "guildmaster": "guild",
    "castellan": "audience",
    "curate": "chapel_nave",
    "anselm": "chapel_nave",
    "maeve": "chapel_vestry",
    "ortho": "chapel_nave",
    "bellan": "chapel_bell",
    "gisla": "chapel_nave",
}
