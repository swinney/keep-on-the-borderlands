"""Keep rooms (zones spec docs/specs/zones/keep.md).

The lawful hub: recall point (Inner Bailey), shops, bank, tavern, and the
chapel. ~26 rooms, no hostile mobs. Pure data — no Evennia import.
"""

from __future__ import annotations

from world.zones.records import RoomRecord

ZONE = "keep"

ROOMS: list[RoomRecord] = [
    {
        "key": "main_gate",
        "name": "Main Gate",
        "zone": ZONE,
        "desc": (
            "Twin square towers flank the iron-bound gate of the Keep. "
            "Crossbowmen watch the road from the murder-slits above, and beyond "
            "the threshold the Borderlands wilderness falls away to the south."
        ),
    },
    {
        "key": "gatehouse",
        "name": "Gatehouse Passage",
        "zone": ZONE,
        "desc": (
            "A short vaulted tunnel pierces the curtain wall. Murder-holes pock "
            "the ceiling and a heavy portcullis hangs ready to drop. The way runs "
            "north into the Keep and south back to the gate."
        ),
    },
    {
        "key": "entry_yard",
        "name": "Entry Yard",
        "zone": ZONE,
        "desc": (
            "A cobbled yard just inside the walls. A weathered notice board and a "
            "bounty board are nailed to the gatehouse, scrawled with warnings and "
            "promises of coin. The Outer Bailey opens to the north."
        ),
    },
    {
        "key": "east_wall",
        "name": "Eastern Wall Walk",
        "zone": ZONE,
        "desc": (
            "The parapet of the eastern wall. From here a sentry can see the dust "
            "of the road and the dark line of the wilds beyond. The bailey lies "
            "below to the west."
        ),
    },
    {
        "key": "west_wall",
        "name": "Western Wall Walk",
        "zone": ZONE,
        "desc": (
            "The western rampart, hard against the cliff the Keep is built upon. "
            "Wind hums through the crenellations. Stairs descend east into the "
            "Outer Bailey."
        ),
    },
    {
        "key": "outer_bailey",
        "name": "Outer Bailey",
        "zone": ZONE,
        "desc": (
            "The broad central ward of the lower Keep, ringed by wall-walks and "
            "busy with traders, soldiers, and adventurers. Lanes radiate to the "
            "shops, the tavern, and the chapel; the inner gate stands to the north."
        ),
    },
    {
        "key": "provisioner",
        "name": "Provisioner's Store",
        "zone": ZONE,
        "desc": (
            "Shelves crowd this snug shop: coils of rope, bundled torches, flasks "
            "of oil, iron rations, and a locked case of holy water. The "
            "provisioner totals sums on a worn abacus."
        ),
    },
    {
        "key": "armorer",
        "name": "Armory",
        "zone": ZONE,
        "desc": (
            "Racks of leather, mail, and a single suit of plate line the walls, "
            "with shields stacked by the door. The armorer taps a breastplate to "
            "show its temper."
        ),
    },
    {
        "key": "weaponsmith",
        "name": "Weaponsmith",
        "zone": ZONE,
        "desc": (
            "Blades, hafts, and bowstaves gleam in ordered rows. The air tastes "
            "of oil and whetstone. The weaponsmith tests an edge against her thumb."
        ),
    },
    {
        "key": "trader",
        "name": "Trader's Post",
        "zone": ZONE,
        "desc": (
            "A cluttered emporium of sundries that buys whatever loot wanderers "
            "drag back from the caves. The trader weighs a handful of gems with a "
            "merchant's careful frown."
        ),
    },
    {
        "key": "bank",
        "name": "Moneychanger & Vault",
        "zone": ZONE,
        "desc": (
            "Behind a stout iron grille the moneychanger keeps ledgers and a "
            "deep, guarded vault. Coin deposited here survives even a fatal trip "
            "into the wilds."
        ),
    },
    {
        "key": "tavern",
        "name": "The One-Eyed Cat",
        "zone": ZONE,
        "desc": (
            "Smoke, ale, and the murmur of rumor fill this low-beamed tavern. "
            "Hard-bitten sell-swords nurse their cups along the benches, waiting "
            "to be hired by anyone with coin and a cause."
        ),
    },
    {
        "key": "inn",
        "name": "The Traveller's Rest",
        "zone": ZONE,
        "desc": (
            "A clean, quiet inn with rooms to let. A night's rest here lets the "
            "weary recover and the learned commit their spells anew to memory."
        ),
    },
    {
        "key": "guild",
        "name": "Guildhall",
        "zone": ZONE,
        "desc": (
            "The adventurers' guildhall, its walls hung with trophy heads and a "
            "board of standing bounties. The Guildmaster sizes up every newcomer "
            "who darkens the door."
        ),
    },
    {
        "key": "chapel_nave",
        "name": "Chapel Nave",
        "zone": ZONE,
        "desc": (
            "A modest stone chapel of the Lawful faith. Candlelight gilds the "
            "altar and the kindly Curate tends a handful of acolytes. A stair "
            "winds up to the bell tower; the vestry lies north."
        ),
    },
    {
        "key": "chapel_vestry",
        "name": "Vestry",
        "zone": ZONE,
        "desc": (
            "A cramped robing room and priest's cell behind the nave. Vestments "
            "hang on pegs and a locked chest sits beneath the narrow cot — a "
            "place where secrets might be hidden."
        ),
    },
    {
        "key": "chapel_bell",
        "name": "Bell Tower",
        "zone": ZONE,
        "desc": (
            "The chapel's bell hangs in an open belfry above the rooftops. The "
            "bellringer keeps watch here, and on a clear night the whole Keep — "
            "and who moves through it after dark — lies spread below."
        ),
    },
    {
        "key": "fountain_sq",
        "name": "Fountain Square",
        "zone": ZONE,
        "desc": (
            "A cheerful little square built around a worn stone fountain where "
            "folk gather to gossip and draw water. Lanes branch off toward the "
            "inn, the bank, the guild, and the chapel."
        ),
    },
    {
        "key": "smith_yard",
        "name": "Smithy Yard",
        "zone": ZONE,
        "desc": (
            "An open work-yard ringing with hammer-blows, smoke drifting from the "
            "forges. The armory, weaponsmith, stables, and bailiff's house all "
            "open onto it."
        ),
    },
    {
        "key": "stables",
        "name": "Common Stables",
        "zone": ZONE,
        "desc": (
            "Straw-strewn stalls house the garrison's mounts and a few hired "
            "mules. A stablehand forks hay while horses stamp and blow."
        ),
    },
    {
        "key": "warehouse",
        "name": "Warehouse",
        "zone": ZONE,
        "desc": (
            "Crates and barrels rise in shadowed rows under a high roof. The "
            "stores of the Keep are kept here, and the quartermaster grumbles "
            "about what has gone missing of late."
        ),
    },
    {
        "key": "bailiff",
        "name": "Bailiff's House",
        "zone": ZONE,
        "desc": (
            "The bailiff keeps order in the lower ward from this trim house. A "
            "duty-roster and a rack of billhooks stand by the door for the watch."
        ),
    },
    {
        "key": "inner_gate",
        "name": "Inner Gatehouse",
        "zone": ZONE,
        "desc": (
            "A second, stronger gate guards the approach to the inner ward. "
            "Steel-helmed guards check all who pass north to the Inner Bailey."
        ),
    },
    {
        "key": "inner_bailey",
        "name": "Inner Bailey",
        "zone": ZONE,
        "desc": (
            "The heart of the Keep, a calm flagged court before the great tower. "
            "This is the safest ground in the Borderlands — and the place to which "
            "the weary and the slain are recalled."
        ),
    },
    {
        "key": "audience",
        "name": "Castellan's Audience Chamber",
        "zone": ZONE,
        "desc": (
            "A vaulted hall hung with banners where the Castellan, lord of the "
            "Keep, hears petitions and dispatches those bold enough to take his "
            "commission against the Caves of Chaos."
        ),
    },
    {
        "key": "keep_tower",
        "name": "Keep Tower",
        "zone": ZONE,
        "desc": (
            "The high overlook atop the great tower. The Corporal of the Watch "
            "scans the wilderness through a brass glass, marking every column of "
            "smoke beyond the walls."
        ),
    },
]
