# Keep on the Borderlands MUD

An open-source persistent multiplayer text MUD adapting Gary Gygax's 1979
module *B2: The Keep on the Borderlands* as the opening campaign arc of a
larger D&D-flavored MUD.

**Status: v1 acceptance-complete.** The full B2 campaign arc is built and
playable — all milestones M0–M16 plus the M17 polish slices are done, and the
v1 acceptance criteria are machine-verified
(`tests/acceptance/test_criteria_coverage.py`). The Keep, Wilderness, Caves of
Chaos, and Shrine zones are populated by a runtime world-build; combat,
factions, henchmen, repop, seasonal resets, the disguised-priest plot, the quest
catalog, and death/hardcore all ship.

**Want to play it?** → **[Run the game](#run-the-game)** below, or the full
[installation & run guide](docs/installation.md).

## What this is

- **Engine:** [Evennia](https://www.evennia.com/) (Python 3, Django ORM).
- **Ruleset:** [Old-School Essentials](https://oldschoolessentials.necroticgnome.com/)
  (B/X retroclone, OGL-compatible).
- **Level range:** 1–10, MUD-scaled from the module's original 1–3.
- **Surface:** Telnet plus Evennia's default web client.
- **Target scale:** 20–50 concurrent players in the B2 content.
- **License:** MIT (see [`LICENSE`](LICENSE)).

## What's interesting about it

Adapting a tabletop module to a persistent multiplayer world means choosing
how the static politics of the Caves of Chaos become *reactive* without
collapsing into either a content treadmill (full persistence) or a soulless
respawn grinder (standard Diku-style 15-minute repop). The interesting
design work lives in:

- A **scripted faction state machine** — tribes hold each other in
  peaceful / tense / war states; player actions shift those states by
  threshold, not by full simulation.
- **Tribe-scoped repop with rival expansion** — killing a chief and shaman
  freezes a tribe for an hour and lets a rival tribe push into the empty
  caves.
- **Seasonal world resets** — player characters and gear persist; world
  state advances and resets on a season cadence.
- **A rotating disguised-spy plot** — each season randomly assigns the
  module's evil priest to one of N chapel NPCs with a randomized clue
  pool, sidestepping the "first player wins the secret forever" problem.
- **Built by Claude Code in a [Ralph
  Loop](https://ghuntley.com/ralph/)** — the spec, test, and
  implementation pipeline is itself a first-class design concern.

See [`CLAUDE.md`](CLAUDE.md) for the full design context, locked decisions,
and Ralph Loop strategy. Architecture decisions live in
[`docs/decisions/`](docs/decisions/).

## Repository layout

```
CLAUDE.md                  Full design context — start here
mudgame/                   The Evennia game directory (run the game from here)
  world/                   Pure rules core, managers, zones, runtime world-build
  typeclasses/             Characters, mobs, objects, scripts
  commands/                In-game commands
  server/, web/            Evennia config + themed web client
tests/                     Spec-derived test suites (one per subsystem)
docs/installation.md       Install & run the game (operator guide)
docs/decisions/            Architecture decision records (ADRs)
docs/specs/                Per-subsystem specifications
Containerfile              Sandboxed environment for the Ralph build loop
Makefile                   Loop convenience targets (build, login, loop, …)
scripts/ralph.sh           The loop runner itself
openspec/                  OpenSpec workspace
keep-on-borderlands-openspec-prompt.md
                           Phase-0 prompt fed to OpenSpec
```

## Run the game

Quick start (full detail, including first-boot world population and connecting,
in the **[installation & run guide](docs/installation.md)**):

```sh
python -m venv .venv && source .venv/bin/activate
pip install -e .            # evennia 6.0.0 + scipy

cd mudgame
evennia migrate            # create the database
evennia start             # first boot builds + populates the whole world
```

Then connect by **telnet** to `localhost:4000`, or open the **web client** at
`http://localhost:4001/`. On first `evennia start` you'll be prompted to create
the superuser (admin) account. See the
[guide](docs/installation.md) for re-populating an existing database, ports, and
troubleshooting.

## Run the build loop (Ralph) — not the game

This is the **autonomous agent loop that built the project**, a separate
workflow from running the game (above). You only need this if you want to drive
or study the build process itself.

Requires rootless [Podman](https://podman.io/) and a Claude Pro or Max
subscription. See [`docs/decisions/0001-container-runtime.md`](docs/decisions/0001-container-runtime.md)
and [`docs/decisions/0002-claude-auth.md`](docs/decisions/0002-claude-auth.md)
for the reasoning.

```sh
make build       # build the container image
make login       # one-time: 'claude login' inside the container
make loop        # start the loop (Ctrl-C to stop)
```

`make help` lists the rest. The loop reads `PROMPT.md` and `tasks.md`; with the
project at v1 acceptance, the remaining `tasks.md` items are deferred polish.

## Contributing

The project is open source from day one. The v1 campaign arc was built
end-to-end by the Ralph Loop against the specs in [`docs/specs/`](docs/specs/);
post-v1 work is deferred polish and hardening (see `tasks.md`). Watch the repo
if you're interested — contribution guidelines will follow as the post-v1
direction settles.

## Acknowledgements

- *B2: The Keep on the Borderlands* by Gary Gygax (1979).
- Old-School Essentials by Necrotic Gnome.
- [Evennia](https://www.evennia.com/), without which this would be a
  much longer project.
