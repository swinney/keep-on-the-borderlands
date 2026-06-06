# Playing the Game

A player's guide to **Keep on the Borderlands** — how to connect, get around, and
use the commands the game actually understands today. It's grounded in the real
command set (`mudgame/commands/`) and the OSE rules in the specs; where a system
is built but not yet exposed as a player flow, this guide says so plainly (see
[Current state & limits](#10-current-state-limits)).

> New here? See the [Install & run guide](installation.md) first to get a server
> up, then connect with a MUD client (Mudlet) on telnet port **4000**, or the web
> client at **`http://<host>:4001/webclient/`**.

---

## 1. Connecting and your character

At the connection screen (before you're logged in):

```
create <name> <password>     # make a new account + character
connect <name> <password>    # log into an existing one
```

Each account has one same-named character. Creating an account makes a normal
**player** (not an admin — only the server's first account is the superuser). On
login you spawn at the **Inner Bailey of the Keep** — the lawful hub and the point
you'll *recall* to. Type `look` to see where you are and `help` for the command
list.

---

## 2. Getting around

| Command | What it does |
| --- | --- |
| `north` `south` `east` `west` `up` `down` (`n` `s` `e` `w` `u` `d`) | move through the room's exits |
| `look` (`l`) | redisplay the room; `look <thing>` to examine something |
| `map` | the coordinate map (the Wilderness and Caves are an xyzgrid) |
| `inventory` (`i`) | what you're carrying |
| `get <item>` / `drop <item>` / `give <item> to <target>` | handle objects |
| `say <msg>` (`"msg`) · `pose <action>` (`:waves`) · `whisper <who> = <msg>` | talk |
| `who` | who's online |
| `help` / `help <command>` | the in-game reference (authoritative for exact syntax) |

`help <command>` is always the source of truth for a command's exact usage — this
guide summarizes, the game itself is definitive.

---

## 3. The Keep — shops, bank, tavern

The Keep is safe (no combat inside, v1) and is where you prepare. You start with
**3d6 × 10 gp** (30–180, rolled at creation).

### Shops
At a vendor's room:

```
list                 # (alias: wares) show what this vendor stocks and prices
buy <item>           # purchase by name (e.g. buy torch)
sell <item>          # sell loot to the Trader (buys at half list price)
```

Vendors and a sample of their stock (full prices via `list`):

- **Provisioner** — `torch` (1), `lantern` (10), `oil_flask` (2), `rope_50ft` (1),
  `rations_standard` (5), `rations_iron` (15), `holy_water` (25), `wolfsbane` (10),
  `garlic` (5), `mirror_steel` (5), `wooden_pole_10ft` (1), `iron_spikes_12` (1),
  `backpack` (5), `waterskin` (1).
- **Weaponsmith** — `dagger` (3), `mace` (5), `short_sword` (7), `sword` (10),
  `two_handed_sword` (15), `spear` (3), `battle_axe` (7), `short_bow` (25),
  `long_bow` (40), `crossbow` (30), `arrows_20` (5).
- **Armorer** — `leather_armor` (20), `chain_mail` (40), `plate_mail` (60),
  `shield` (10).

### Bank (in the bank room)
The bank is **death-safe** — coin on deposit is never lost to a corpse run.

```
balance              # carried coin + bank balance
deposit <amount>     # move coin into the bank
withdraw <amount>    # take coin out
```

---

## 4. Henchmen — how you adventure solo

Hire NPC companions at the **tavern** (canon to B2). They follow, fight, and take a
share — the way a lone player survives the Caves.

```
roster                       # (alias: recruits) the tavern's hireable henchmen
hire <name>                  # recruit one
order <henchman> follow      # standing orders:
order <henchman> attack <target>
order <henchman> guard <who>
order <henchman> wait
order <henchman> retreat
order <henchman> dismiss
```

Hiring rolls an **OSE reaction** (`2d6` + your Charisma modifier): a poor result
means they decline (no fee charged); a good result charges the **hire fee** and
they join. You can't exceed your **retainer cap** (set by your Charisma). Henchmen
have **loyalty** and make **morale** checks — they can flee or refuse orders when a
fight goes badly (first casualty, party at half strength). Henchman death is
**permanent**.

---

## 5. Combat

Combat is OSE with **ascending AC**. Before a fight:

```
consider <target>            # gauge how dangerous it is + your faction standing
```

Then engage:

```
attack <target>              # aliases: kill, hit
```

Each `attack` resolves one melee swing: roll `1d20` + attack bonus + Strength
modifier vs. the target's AC. A **natural 20 always hits**, a **natural 1 always
misses**.

> **Current combat note.** Equipped weapons and armor don't modify damage/AC yet
> (a later milestone). Unarmed damage is a placeholder `1d6`, and AC currently
> comes from Dexterity only — so a `sword` you buy is yours to carry, but it
> doesn't change your numbers in this build. See
> [Current state & limits](#10-current-state-limits).

**PvP is disabled in v1** — you can't attack other players.

---

## 6. Spells (Magic-Users, Elves, Clerics)

Magic is **Vancian** (OSE): you memorize spells while resting, then spend them.

```
rest                         # aliases: memorize, pray — fill your spell slots
cast <spell name>            # untargeted (e.g. light, detect evil) — affects your room
cast <spell name> at <target>   # targeted (e.g. magic missile, cure light wounds)
cast <spell name> <target>      # same, shorthand
```

`rest` refills slots from your spellbook (Magic-User / Elf) or the full divine
list (Cleric); non-casters just recover. In combat, casting is **declared** for the
round and resolves at the round's end — **if you take damage before it resolves,
the spell is disrupted and the slot is lost.** Protect your casters.

---

## 7. Quests, factions, and the plot

### Quests
Quest-givers live in the Keep (the Guildmaster, the Castellan, the Corporal of the
Watch):

```
quests                       # (alias: bounties) your quest log
accept <quest>               # take a quest from a giver
turnin <quest>               # (alias: turn-in) claim the reward once complete
```

### Factions
The Caves' tribes hold per-pair relationships (**allied / peaceful / tense / war**)
and track a standing toward *you* (**friendly → neutral → hostile →
kill-on-sight**). `consider <target>` shows your standing. Your deeds move it —
killing a tribe's members hardens them against you and can shift tribe-vs-tribe
politics. Completing quests can aid or harm factions too.

### The disguised priest
Each season, one of the Keep chapel's NPCs is secretly an evil-Chaos spy. You can
expose them via high-level **Detect Evil**, the **Curate's** dialogue, witnessing a
**nighttime act**, or finding a **planted object** — then **report to the
Castellan**. Doing so triggers a server-wide event (the spy flees to the Shrine and
becomes a boss). Identity and clues reset each season.

---

## 8. Death

When you hit 0 HP, one of two models applies:

- **Default (forgiving):** you lose XP back to the **start of your current level**
  (you don't de-level), your **corpse** stays at the death spot holding all your
  gear and carried coin, and you recall to the **Inner Bailey** at 1 HP. Walk back
  to your corpse to recover your things — a *corpse run*. (Banked coin is safe.)
- **Hardcore (opt-in, irreversible):** the character is **deleted** on death and
  added to the server **leaderboard** (final level + season). Marked `[HC]` in the
  who-list. This is a deliberate choice made at creation and can never be undone.

---

## 9. The world & how it lives

The campaign runs **Keep → Wilderness → Caves of Chaos → Shrine of Evil Chaos**.
The Caves are tribe territory; the Shrine is the deep end (some rooms block recall).

- **Recall** always returns you to the Inner Bailey.
- **Repop:** ordinary monsters respawn every **15 minutes**. Kill a tribe's **chief
  *and* shaman** and that tribe's repop **freezes for 60 minutes** — during that
  window a rival tribe may send scouts into the empty caves and the political map
  can shift. The Shrine resets on a 24-hour cycle.
- **Seasons:** the world runs in 6-week seasons. Your character, XP, gear, bank,
  and the leaderboard persist across a reset; faction states, repop, the Shrine,
  and the disguised-priest identity roll over.

---

## Worked examples

Illustrative sessions. The **commands, room names, exits, item names, and prices
are real**; the room descriptions and exact line formatting are paraphrased (your
client and theme will differ).

### Travelling from your spawn to a shop

You spawn in the **Inner Bailey**. To reach the Provisioner's Store, head out
through the gates — the shops ring the Outer Bailey:

```
> look
Inner Bailey
(the keep's inner courtyard — the recall point)
Exits: south (Inner Gatehouse), east (Castellan's Audience Chamber), up (Keep Tower)

> south
Inner Gatehouse

> south
Outer Bailey
Exits: north (Inner Gatehouse), south (Entry Yard), east (Eastern Wall Walk),
       west (Western Wall Walk), northeast (Fountain Square), northwest (Smithy Yard),
       southeast (The One-Eyed Cat), southwest (Provisioner's Store)

> southwest
Provisioner's Store
```

To **leave the Keep** for the Wilderness and the Caves instead, go the other way
from the Outer Bailey: `south` → Entry Yard, `south` → Gatehouse Passage, `south`
→ Main Gate.

### Exploring an area

Read the room with `look`, walk its exits to map it, and `look <thing>` to inspect
what you see. `map` renders the coordinate grid for the Wilderness and Caves.

```
> look
Outer Bailey
(the broad muster yard; the hub of the Keep)
Exits: north, south, east, west, northeast, northwest, southeast, southwest
You see: a man-at-arms

> look man
(a description of the guard)

> northeast
Fountain Square
Exits: north (The Traveller's Rest), south (Moneychanger & Vault),
       east (Guildhall), west (Chapel Nave), southeast (Trader's Post)

> map
(the grid map — most useful out in the Wilderness and the Caves of Chaos)
```

Tip: every room lists its exits; follow them to learn an area, and use `look` on
NPCs, features, or items before you interact.

### Interacting with a shop

At the **Provisioner's Store**, list the wares, buy, and check your pack:

```
> list
Wares for sale:
  torch - 1 gp
  oil_flask - 2 gp
  rope_50ft - 1 gp
  rations_standard - 5 gp
  lantern - 10 gp
  holy_water - 25 gp
  ... (and more)

> buy torch
You buy torch for 1 gp. You have 104 gp left.

> buy lantern
You buy lantern for 10 gp. You have 94 gp left.

> inventory
You are carrying:
  torch
  lantern
```

Sell loot back at the **Trader's Post** (off Fountain Square, `southeast`) — the
Trader is the one vendor that *buys*, at half the list price:

```
> sell dagger
You sell dagger for 1 gp.
```

If a vendor doesn't stock an item you try to buy: `I don't deal in that.` If you
can't afford it: `You can't afford that (40 gp).`

---

## 10. Current state & limits

This is an honest snapshot of what is and isn't a player-facing flow today. The
underlying systems are built and tested; some front-ends aren't wired yet.

- **No in-game character creation beyond `create`.** A new character has flat
  ability scores (all 10), 1 HP, and **no class** — race/class selection and stat
  rolling aren't exposed as player commands yet. To play a specific class (e.g. to
  cast spells), a server admin currently sets it (via the `py` command). Class
  options that exist in the rules: Cleric, Fighter, Magic-User, Thief, and the
  race-classes Dwarf, Elf, Halfling (no multiclass).
- **No leveling UI yet.** XP is tracked and the 1–10 range exists in the rules, but
  there's no in-game level-up flow.
- **Equipment is a placeholder in combat.** You can buy/carry weapons and armor,
  but they don't yet modify damage (unarmed `1d6`) or AC (Dexterity only).
- **PvP is disabled** in v1.

None of these block exploring the full built world, shopping, hiring henchmen,
fighting mobs, taking quests, and seeing the faction and plot systems react — they
just mark where the RPG character layer is still coming.

---

## Command quick reference

| Command (aliases) | Category | Usage |
| --- | --- | --- |
| `look` (`l`) | move | `look` / `look <thing>` |
| `n/s/e/w/u/d` | move | walk an exit |
| `map` | move | show the grid map |
| `inventory` (`i`) | items | list what you carry |
| `get` / `drop` / `give` | items | `get <item>` … |
| `say` / `pose` / `whisper` / `who` | social | communicate |
| `list` (`wares`) | shop | vendor stock + prices |
| `buy` / `sell` | shop | `buy <item>` / `sell <item>` |
| `balance` / `deposit` / `withdraw` | bank | `deposit <amount>` … |
| `roster` (`recruits`) | henchmen | hireable recruits (tavern) |
| `hire` | henchmen | `hire <name>` |
| `order` | henchmen | `order <henchman> follow\|attack <t>\|guard <who>\|wait\|retreat\|dismiss` |
| `consider` | combat | `consider <target>` |
| `attack` (`kill`, `hit`) | combat | `attack <target>` |
| `cast` | combat | `cast <spell> [at <target>]` |
| `rest` (`memorize`, `pray`) | general | refill spell slots / recover |
| `quests` (`bounties`) | quests | your quest log |
| `accept` | quests | `accept <quest>` |
| `turnin` (`turn-in`) | quests | `turnin <quest>` |
| `help` | — | `help` / `help <command>` |
