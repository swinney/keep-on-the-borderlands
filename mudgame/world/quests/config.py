"""Quest catalog + tuning — the full B2 quest catalog (docs/specs/quests.md §1-§8).

This is the single data/balance file for the quest catalog (M13): every quest
record, its giver, prerequisites, reward, and the cross-system effects (faction
standing/tension, the cult-aiding chain, the two season-global quests). All of it
is pure data — no Evennia imports — so the catalog is unit-testable without
booting the server. *Enforcement* lives elsewhere: the per-character state machine
(``world.quests.state``) derives availability; the faction/priest/season managers
fire the effects; ``commands.quests`` and ``typeclasses.npcs`` wire the givers.

Count note: ``docs/specs/quests.md``'s prose summary says "24 quests", but the
authoritative §2-§7 tables enumerate 26 distinct quest ids. The tables are the
testable contract, so every enumerated quest is wired here and ``CATALOG`` holds
26 records; the "24" is a stale prose tally, not a requirement to drop content.
"""

from __future__ import annotations

from dataclasses import dataclass

# ── Giver keys ───────────────────────────────────────────────────────────────
# Stable NPC keys; they mirror the world's NPC/mob keys where one exists
# (placements in docs/specs/zones/). The rotating disguised priest has no fixed
# NPC, so its quests use the ``SPY`` sentinel; the engine resolves it to whichever
# chapel NPC is the spy this season (R4, docs/specs/disguised-priest.md).
CASTELLAN = "castellan"
CURATE = "curate"
GUILDMASTER = "guildmaster"
PROVISIONER = "provisioner"
HERMIT = "mad_hermit"
ORC_VOL_CHIEF = "orc_vol_chief"
ORC_DEC_CHIEF = "orc_dec_chief"
GOBLIN_CHIEF = "goblin_chief"
SPY = "spy"

#: Every distinct giver key in the catalog, in catalog order.
GIVERS: tuple[str, ...] = (
    GUILDMASTER,
    CASTELLAN,
    CURATE,
    PROVISIONER,
    HERMIT,
    ORC_VOL_CHIEF,
    ORC_DEC_CHIEF,
    GOBLIN_CHIEF,
    SPY,
)

# ── Season-global effect tags (quests.md §8) ─────────────────────────────────
# A quest's ``season_global`` carries one of these; the engine turn-in fires the
# matching server-wide event (both reset at the season boundary, R6).
SEASON_EXPOSE_PRIEST = "expose_priest"  # report the spy → global "exposed" event (R4)
SEASON_END_SEASON = "end_season"  # destroy the Altar of Chaos → end_season (R6)

# A repeatable bounty returns to ``available`` this long after a turn-in
# (quests.md §1). 15 real minutes mirrors the standard repop window (repop.md §1)
# — a tuning knob, not a locked decision.
BOUNTY_COOLDOWN_SECONDS = 15 * 60


@dataclass(frozen=True)
class KillStep:
    """A "kill N of faction F" objective (quests.md §1 ``steps``).

    ``target`` optionally narrows the objective to a specific named mob — a tribe
    leader, the owlbear, the minotaur — while ``None`` means any member of
    ``faction`` counts. The pure kill-tracker credits by ``faction``; honouring
    ``target`` (so only the named leader's death counts) is an engine concern
    wired with the mob-death hook in a later M13 slice.
    """

    faction: str
    count: int
    target: str | None = None


@dataclass(frozen=True)
class DeedStep:
    """A non-kill objective resolved by a world event, not the kill-tracker.

    ``kind`` is one of the spec's objective verbs (quests.md §1: fetch / escort /
    report / deliver / donate / bribe / enter); ``detail`` is the human-readable
    goal. A deed carries no per-faction kill progress, so the pure state machine
    ignores it — completion is driven by the engine event that satisfies the deed.
    """

    kind: str
    detail: str


#: A quest objective is either a kill-count step or a world-event deed.
Step = KillStep | DeedStep


@dataclass(frozen=True)
class QuestReward:
    """What a quest pays on turn-in (quests.md §1 ``rewards``).

    A bounty pays its ``gp`` as coin; the OSE treasure-as-XP link (economy.md §6)
    turns that coin into XP when the player secures it in the Keep or banks it.
    ``xp`` is a direct-grant seam (``0`` for the bounties, whose XP arrives through
    the secure loop). ``items`` lists named reward items (holy water, a map, a
    relic) granted on completion.
    """

    gp: int = 0
    xp: int = 0
    items: tuple[str, ...] = ()


@dataclass(frozen=True)
class StandingGate:
    """A minimum faction standing required for a quest to be offered (quests.md §6).

    ``min_band`` is a label from ``world.factions.config.STANDING_LADDER`` (e.g.
    ``"neutral"``). Tribe-chief quests are offered only at *non-hostile* standing
    with the giver tribe; this records that gate as data for the state machine to
    enforce.
    """

    faction: str
    min_band: str


@dataclass(frozen=True)
class Quest:
    """A full quest record (quests.md §1).

    Prerequisites (``min_level``, ``prereq_quests``, ``standing_gates``,
    ``requires_evidence``) gate availability; the completion-effect fields encode
    the cross-system side effects summarised in quests.md §8. Both are data here —
    the state machine and the managers act on them.
    """

    id: str
    giver: str
    title: str
    steps: tuple[Step, ...]
    reward: QuestReward
    repeatable: bool = False
    # ── prerequisites (quests.md §1 ``prereqs``) ─────────────────────────────
    min_level: int = 1
    prereq_quests: tuple[str, ...] = ()
    standing_gates: tuple[StandingGate, ...] = ()
    # Gated on per-character priest evidence rather than level/quest (R4):
    # c_expose_priest needs a valid proof, cu_suspicions ≥2 clue sightings.
    requires_evidence: bool = False
    # ── completion effects (quests.md §8) ────────────────────────────────────
    harm_faction: str | None = None  # R2 quest_harm: standing - with this faction
    aid_faction: str | None = None  # R2 quest_aid: standing + with this faction
    tension_pair: tuple[str, str] | None = None  # R2 quest_aid_vs: pair tension +
    breaks_alliance: tuple[str, str] | None = None  # bribe the ogre: break the alliance
    aids_cult: bool = False  # R4 cult-aiding chain (3rd completion → Caves ambush)
    season_global: str | None = None  # SEASON_EXPOSE_PRIEST | SEASON_END_SEASON


def _quest(quest: Quest) -> tuple[str, Quest]:
    """Index helper: pair a quest with its id for the ``CATALOG`` dict build."""
    return quest.id, quest


CATALOG: dict[str, Quest] = dict(
    _quest(q)
    for q in (
        # ── Guildmaster — combat bounties, all repeatable (quests.md §2) ──────
        Quest(
            id="g_kobold_cull",
            giver=GUILDMASTER,
            title="Cull the Kobolds",
            steps=(KillStep(faction="kobold", count=8),),
            reward=QuestReward(gp=50),
            repeatable=True,
            min_level=1,
            harm_faction="kobold",
        ),
        Quest(
            id="g_orc_vile",
            giver=GUILDMASTER,
            title="Break the Vile Rune",
            steps=(KillStep(faction="orc_vol", count=1, target="orc_vol_chief"),),
            reward=QuestReward(gp=150),
            repeatable=True,
            min_level=2,
            harm_faction="orc_vol",
        ),
        Quest(
            id="g_orc_dec",
            giver=GUILDMASTER,
            title="Break the Decapitators",
            steps=(KillStep(faction="orc_dec", count=1, target="orc_dec_chief"),),
            reward=QuestReward(gp=150),
            repeatable=True,
            min_level=2,
            harm_faction="orc_dec",
        ),
        Quest(
            id="g_bugbear_chief",
            giver=GUILDMASTER,
            title="The Bugbear Grosh",
            steps=(KillStep(faction="bugbear", count=1, target="bugbear_chief"),),
            reward=QuestReward(gp=200),
            repeatable=True,
            min_level=3,
            harm_faction="bugbear",
        ),
        Quest(
            id="g_gnoll_chief",
            giver=GUILDMASTER,
            title="The Gnoll Pack-Lord",
            steps=(KillStep(faction="gnoll", count=1, target="gnoll_chief"),),
            reward=QuestReward(gp=200),
            repeatable=True,
            min_level=3,
            harm_faction="gnoll",
        ),
        Quest(
            id="g_hobgoblin_king",
            giver=GUILDMASTER,
            title="The Head of King Nardo",
            steps=(KillStep(faction="hobgoblin", count=1, target="hobgoblin_king"),),
            reward=QuestReward(gp=350, items=("a fine weapon",)),
            repeatable=True,
            min_level=4,
            harm_faction="hobgoblin",
        ),
        Quest(
            id="g_owlbear",
            giver=GUILDMASTER,
            title="The Caged Horror",
            steps=(KillStep(faction="owlbear", count=1, target="owlbear"),),
            reward=QuestReward(gp=175),
            repeatable=True,
            min_level=3,
        ),
        Quest(
            id="g_minotaur",
            giver=GUILDMASTER,
            title="Into the Maze",
            steps=(KillStep(faction="minotaur", count=1, target="minotaur"),),
            reward=QuestReward(gp=300, items=("a map to the Shrine",)),
            repeatable=True,
            min_level=5,
        ),
        # ── Castellan — authority & story (quests.md §3) ─────────────────────
        Quest(
            id="c_scout_caves",
            giver=CASTELLAN,
            title="Scout the Ravine",
            steps=(DeedStep(kind="enter", detail="enter the Caves ravine and return"),),
            reward=QuestReward(gp=40),
            min_level=1,
        ),
        Quest(
            id="c_rescue_soldier",
            giver=CASTELLAN,
            title="The Captured Soldier",
            steps=(
                DeedStep(kind="escort", detail="free the captive in the orc_dec cave and escort"),
            ),
            reward=QuestReward(gp=120),
            min_level=2,
            aid_faction="keep",
        ),
        Quest(
            id="c_expose_priest",
            giver=CASTELLAN,
            title="Treachery in the Chapel",
            steps=(DeedStep(kind="report", detail="report the spy to the Castellan with proof"),),
            reward=QuestReward(gp=250, items=("the title 'Unmasker of the Cult'",)),
            requires_evidence=True,
            season_global=SEASON_EXPOSE_PRIEST,
        ),
        Quest(
            id="c_destroy_shrine",
            giver=CASTELLAN,
            title="Cleanse the Shrine",
            steps=(DeedStep(kind="report", detail="destroy the Altar of Chaos"),),
            reward=QuestReward(gp=1000, items=("a holy relic",)),
            min_level=7,
            prereq_quests=("g_minotaur",),
            season_global=SEASON_END_SEASON,
        ),
        # ── Curate — chapel & detection (quests.md §4) ───────────────────────
        Quest(
            id="cu_holy_water",
            giver=CURATE,
            title="Vials of the Faithful",
            steps=(DeedStep(kind="fetch", detail="bring 3 empty vials"),),
            reward=QuestReward(items=("holy water", "holy water", "holy water")),
            min_level=1,
        ),
        Quest(
            id="cu_suspicions",
            giver=CURATE,
            title="The Curate's Doubt",
            steps=(DeedStep(kind="report", detail="hear the Curate's suspicions"),),
            reward=QuestReward(items=("a clue to the spy",)),
            # Gated on ≥2 clue sightings (R4), enforced via priest evidence.
            requires_evidence=True,
            min_level=1,
        ),
        Quest(
            id="cu_bless_blades",
            giver=CURATE,
            title="Consecrated Steel",
            steps=(DeedStep(kind="donate", detail="donate 100 gp to the chapel"),),
            reward=QuestReward(items=("a blessed weapon",)),
            min_level=3,
        ),
        # ── Provisioner & Hermit (quests.md §5) ──────────────────────────────
        Quest(
            id="p_caravan",
            giver=PROVISIONER,
            title="The Stolen Caravan",
            steps=(DeedStep(kind="fetch", detail="recover the goods from the bugbears"),),
            reward=QuestReward(gp=130),
            min_level=2,
            harm_faction="bugbear",
        ),
        Quest(
            id="p_supplies",
            giver=PROVISIONER,
            title="Supplies for the Hermit",
            steps=(DeedStep(kind="deliver", detail="deliver rations to the hermit"),),
            reward=QuestReward(gp=30),
            min_level=1,
        ),
        Quest(
            id="h_rare_herb",
            giver=HERMIT,
            title="The Hermit's Errand",
            steps=(DeedStep(kind="fetch", detail="fetch the 'rare herb' (a trap)"),),
            reward=QuestReward(items=("a worthless trinket",)),
            prereq_quests=("p_supplies",),
            min_level=1,
        ),
        Quest(
            id="h_lions",
            giver=HERMIT,
            title="Trouble in the Hills",
            steps=(KillStep(faction="beast", count=1, target="mountain_lion"),),
            reward=QuestReward(gp=80),
            # "befriended": the hermit warms to a player who first runs his supplies.
            prereq_quests=("p_supplies",),
            min_level=1,
        ),
        # ── Tribe chiefs — faction-gated, escalate the rivalry (quests.md §6) ─
        Quest(
            id="t_vol_vs_dec",
            giver=ORC_VOL_CHIEF,
            title="Blood for the Vile Rune",
            steps=(KillStep(faction="orc_dec", count=6),),
            reward=QuestReward(items=("orc loot",)),
            standing_gates=(StandingGate(faction="orc_vol", min_band="neutral"),),
            tension_pair=("orc_vol", "orc_dec"),
            aid_faction="orc_vol",
        ),
        Quest(
            id="t_dec_vs_vol",
            giver=ORC_DEC_CHIEF,
            title="The Decapitator's Due",
            steps=(KillStep(faction="orc_vol", count=6),),
            reward=QuestReward(items=("orc loot",)),
            standing_gates=(StandingGate(faction="orc_dec", min_band="neutral"),),
            tension_pair=("orc_dec", "orc_vol"),
            aid_faction="orc_dec",
        ),
        Quest(
            id="t_gob_vs_gnoll",
            giver=GOBLIN_CHIEF,
            title="Goblin Vengeance",
            steps=(KillStep(faction="gnoll", count=1, target="gnoll_shaman"),),
            reward=QuestReward(items=("a gem cache",)),
            standing_gates=(StandingGate(faction="goblin", min_band="neutral"),),
            tension_pair=("goblin", "gnoll"),
        ),
        Quest(
            id="t_bribe_ogre",
            giver=GOBLIN_CHIEF,
            title="Coin for the Ogre",
            steps=(DeedStep(kind="bribe", detail="bribe the ogre to leave"),),
            reward=QuestReward(),
            standing_gates=(StandingGate(faction="goblin", min_band="neutral"),),
            breaks_alliance=("goblin", "ogre"),
        ),
        # ── Disguised priest — the cult chain, flagged aids_cult (quests.md §7) ─
        Quest(
            id="sp_package",
            giver=SPY,
            title="A Sealed Errand",
            steps=(DeedStep(kind="deliver", detail="deliver a sealed package to a Caves drop"),),
            reward=QuestReward(gp=60),
            aids_cult=True,
        ),
        Quest(
            id="sp_reagent",
            giver=SPY,
            title="Herbs for the Infirmary",
            steps=(DeedStep(kind="fetch", detail="fetch a (poison) reagent from the swamp"),),
            reward=QuestReward(gp=70),
            prereq_quests=("sp_package",),
            aids_cult=True,
        ),
        Quest(
            id="sp_minister",
            giver=SPY,
            title="Mercy for a Prisoner",
            steps=(DeedStep(kind="deliver", detail="minister to a captured cultist in the cells"),),
            reward=QuestReward(gp=80),
            prereq_quests=("sp_reagent",),
            aids_cult=True,
        ),
    )
)

# A stable, immutable view of the ids in catalog order (tests / iteration).
CATALOG_IDS: tuple[str, ...] = tuple(CATALOG)


def quests_from(giver: str) -> list[Quest]:
    """Every catalog quest offered by NPC ``giver``, in stable catalog order."""
    return [quest for quest in CATALOG.values() if quest.giver == giver]
