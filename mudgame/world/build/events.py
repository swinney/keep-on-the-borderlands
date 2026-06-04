"""World-event deed hooks (world-build spec §9, M13 review F3).

The runtime triggers that flip a deed-only quest's completion flag — the seam M13
deferred to this layer. M13 closed the deed-quest turn-in exploit by gating a
deed-only quest's turn-in on ``QuestEntry.deed_done``, set only by
``world.quests.state.record_deed``; the world events that *call* it were left for
the world-build phase. Each hook here finds a character's quest log and records
the matching deed.

The hooks are called from in-world object/room behaviour — the Altar shattering,
a carried delivery item arriving, the escorted captive reaching the Keep, the
spy's package dropped at the Caves drop (spec §9 table). The behaviour imports the
hook lazily; this module imports only the pure ``world.quests.state`` (no
command-layer dependency), preserving the architecture §3 ``managers → build →
zones/rules`` direction. Of those four triggers only the Altar exists as a live
object today; the delivery item, the escort captive, and the spy package are
frozen content (spec §1 non-goals — M15 brings content to life, it does not author
it), so their hooks are delivered and tested at the seam, ready for those carriers
to call once they are built.

Design rules (spec §9):
  * a hook is a **no-op for any character without that quest accepted** — it never
    errors on the common case, mirroring the kill-credit ``Mob._credit_quest_kill``;
  * the shrine-destroyed hook sets *only* the deed flag — it must **not** fire
    ``end_season``. The canonical R6 season-ender is ``Altar.at_destruction``
    itself (review F4), so the altar stays the sole season-ending trigger.
"""

from __future__ import annotations

from typing import Any

from world.quests import state as quest_state

# Deed quest ids whose completion a world event signals (spec §9 table). Each maps
# one in-world trigger to the quest whose ``deed_done`` flag it sets.
SHRINE_DESTROYED_QUEST = "c_destroy_shrine"  # the Altar shatters
RATIONS_DELIVERED_QUEST = "p_supplies"  # rations reach the hermit
CAPTIVE_ESCORTED_QUEST = "c_rescue_soldier"  # the freed soldier reaches the Keep
SPY_PACKAGE_QUEST = "sp_package"  # the spy's package reaches its Caves drop


def credit_deed(character: Any, quest_id: str) -> bool:
    """Mark ``quest_id``'s deed done on ``character``'s quest log; return whether it changed.

    The shared core of every deed hook: read the character's quest log, call the
    pure ``record_deed``, and write the log back only when it flipped an *active*
    entry's flag (so the common case — a bystander without the quest — touches no
    DB). A no-op, never an error, for a missing character, a non-player (a mob), or
    a character without the quest accepted — mirroring ``Mob._credit_quest_kill``.
    """
    if character is None or getattr(character, "IS_MOB", False):
        return False
    log = dict(character.db.quests or {})
    if quest_state.record_deed(log, quest_id):
        character.db.quests = log
        return True
    return False


def shrine_destroyed(character: Any) -> bool:
    """Flag the Altar-shattering deed for ``character`` (``c_destroy_shrine``; spec §9).

    Called from ``Altar.at_destruction`` *in addition to* that hook's ``end_season``
    firing. It sets only the deed-completion flag so the quest turn-in grants its
    reward (review F4); it does not — and must not — fire ``end_season``, leaving
    the altar the sole season-ender.
    """
    return credit_deed(character, SHRINE_DESTROYED_QUEST)


def rations_delivered(character: Any) -> bool:
    """Flag the supply-delivery deed for ``character`` (``p_supplies``; spec §9).

    Called when the carried rations reach the Mad Hermit (delivery item arrival or
    a ``give`` to the hermit). No-op until that carrier object exists (spec §1).
    """
    return credit_deed(character, RATIONS_DELIVERED_QUEST)


def captive_escorted(character: Any) -> bool:
    """Flag the escort deed for ``character`` (``c_rescue_soldier``; spec §9).

    Called when the freed soldier reaches the Keep (the escort NPC's arrival hook).
    No-op until that escort NPC exists (spec §1).
    """
    return credit_deed(character, CAPTIVE_ESCORTED_QUEST)


def spy_package_delivered(character: Any) -> bool:
    """Flag the spy-package deed for ``character`` (``sp_package``; spec §9).

    Called when the spy's sealed package reaches its Caves drop — the first link of
    the cult-aiding chain (disguised-priest spec). No-op until that package object
    exists (spec §1).
    """
    return credit_deed(character, SPY_PACKAGE_QUEST)
