"""Quest catalog + tuning — M9 Guildmaster tribe-clearing slice (docs/specs/quests.md §2).

The full 24-quest catalog lands in M13; this slice defines the one Guildmaster
bounty the M9 vertical slice needs end to end: ``g_kobold_cull`` ("Cull the
Kobolds") — kill 8 kobolds for 50 gp, lowering kobold standing. Every quest
tuning value (kill counts, rewards, the repeatable-bounty cooldown) lives here so
a single file balances the quest economy (CLAUDE.md §3).
"""

from __future__ import annotations

from dataclasses import dataclass

# The Guildmaster's stable NPC key (placement in docs/specs/zones/keep.md).
GUILDMASTER = "guildmaster"

# A repeatable bounty returns to ``available`` this long after a turn-in
# (quests.md §1). 15 real minutes mirrors the standard repop window (repop.md §1)
# — a tuning knob, not a locked decision.
BOUNTY_COOLDOWN_SECONDS = 15 * 60


@dataclass(frozen=True)
class KillStep:
    """A "kill N of faction F" objective (quests.md §1 ``steps``)."""

    faction: str
    count: int


@dataclass(frozen=True)
class QuestReward:
    """Coin/XP a quest pays on turn-in (quests.md §1 ``rewards``).

    A Guildmaster bounty pays its ``gp`` as coin; the OSE treasure-as-XP link
    (economy.md §6) then turns that coin into XP when the player secures it in
    the Keep or banks it — the M9 "treasure→XP-on-secure loop". ``xp`` is a
    direct-grant seam kept for the broader M13 catalog and is ``0`` for the
    kobold cull, whose XP arrives entirely through the secure loop.
    """

    gp: int = 0
    xp: int = 0


@dataclass(frozen=True)
class Quest:
    """A quest record (quests.md §1), narrowed to the M9 kill-bounty shape."""

    id: str
    giver: str
    title: str
    steps: tuple[KillStep, ...]
    reward: QuestReward
    # Faction whose standing drops on completion (R2 ``quest_harm``); None = no shift.
    harm_faction: str | None = None
    repeatable: bool = True
    min_level: int = 1


CATALOG: dict[str, Quest] = {
    "g_kobold_cull": Quest(
        id="g_kobold_cull",
        giver=GUILDMASTER,
        title="Cull the Kobolds",
        steps=(KillStep(faction="kobold", count=8),),
        reward=QuestReward(gp=50, xp=0),
        harm_faction="kobold",
        repeatable=True,
        min_level=1,
    ),
}


def quests_from(giver: str) -> list[Quest]:
    """Every catalog quest offered by NPC ``giver``, in stable catalog order."""
    return [quest for quest in CATALOG.values() if quest.giver == giver]
