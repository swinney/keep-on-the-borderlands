# Installation & Run Guide

A complete, operator-facing guide to **install and run the actual game** — the
B2: Keep on the Borderlands MUD. By the end you will have a populated world
booted on your machine and a client connected to it.

> Looking to run the **Ralph build loop** (the autonomous agent that *built*
> this project) instead of the game? That is a different workflow — see
> [Running the Ralph Loop](#running-the-ralph-loop-not-the-game) at the bottom,
> or the [container/loop strategy doc](ralph-loop.md).

This guide is grounded in the project's real entry points. Where a step depends
on your environment (interactive prompts, host/firewall specifics) it is called
out explicitly.

---

## 1. Prerequisites

- **Python ≥ 3.12** (required by `pyproject.toml`, `requires-python = ">=3.12"`).
- **pip** and a **virtual environment** tool (`venv` ships with Python).
- A C toolchain is not required for a normal install; Evennia and its
  dependencies ship wheels for common platforms.
- ~250 MB of disk for the dependency tree (Evennia pulls in Django and Twisted)
  plus the SQLite database the game creates on first boot.

Verify your Python:

```sh
python --version      # must print 3.12 or newer
```

---

## 2. Install

Clone the repository and install it (editable) into a virtual environment. The
runtime dependencies — `evennia==6.0.0` and `scipy` — are declared in
`pyproject.toml` and pulled in automatically.

```sh
git clone https://github.com/swinney/keep-on-the-borderlands.git
cd keep-on-the-borderlands

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -e .                   # installs evennia 6.0.0 + scipy
```

Confirm the Evennia launcher is on your path:

```sh
evennia --version                  # should print 6.0.0
```

> **Optional — dev/test tooling.** To run the test suite or the gate locally,
> install the dev extras: `pip install -e ".[dev]"` (adds `pytest`,
> `pytest-django`, `ruff`, `mypy`). This is **not** needed just to play the game.

---

## 3. The game directory

All `evennia` launcher commands are run from inside the **game directory**,
which in this repo is `mudgame/`. It holds the Evennia settings, the world
packages (`world/`), typeclasses, and commands.

```sh
cd mudgame
```

Run every command in the rest of this guide from inside `mudgame/` unless noted.

---

## 4. Initialise the database

Evennia stores all persistent state (accounts, characters, XP, gear, bank,
world objects) in a database — SQLite by default, created in the game
directory. Create the schema with Django's migrations:

```sh
evennia migrate
```

This is safe to re-run; it only applies pending migrations.

---

## 5. First boot — the world builds itself

The first time the server ever starts on a fresh database, Evennia runs its
one-time `at_initial_setup()` hook. This project wires that hook to build and
populate the entire world:

- `mudgame/server/conf/at_initial_setup.py` calls
  `world.build.orchestrator.build_all()`.
- `build_all()` brings up the four global managers (faction, repop, season,
  priest), builds every zone in dependency order (Keep → Wilderness → Caves →
  Shrine), registers spawn points, and runs the initial population pass that
  materialises one live mob per spawn point (including each tribe's chief and
  shaman). See the [world-build spec](specs/world-build.md) for detail.

Start the server:

```sh
evennia start
```

On the **very first** `evennia start`, Evennia interactively prompts you to
create the **superuser** (the server-owner / god account) — a username, an
optional email, and a password. Provide them; this account is account #1 and
has full admin rights in-game.

> **Note — the build runs once.** `at_initial_setup()` fires only on the first
> boot of a brand-new database. Tracebacks inside it are silently swallowed by
> Evennia, so if the world looks empty after first boot, see
> [Re-populating an existing database](#8-re-populating-an-existing-database).

Useful lifecycle commands (all from `mudgame/`):

```sh
evennia status     # is the server running?
evennia reload     # hot-reload code without disconnecting players
evennia stop       # shut the server down
```

---

## 6. Connect to the game

The server listens on Evennia's default ports (unchanged by this project):

| Surface | Address | Port |
| --- | --- | --- |
| Telnet (text client) | `localhost` | **4000** |
| Web client + website | `http://localhost:4001/` | **4001** |
| Web client (websocket) | (used by the browser automatically) | 4002 |

### Telnet

```sh
telnet localhost 4000
```

You will see the themed connection screen (the project's MOTD, set in
`mudgame/server/conf/connection_screens.py`). From there:

```
connect <username> <password>     # log in (e.g. your superuser)
create  <username> <password>     # create a new player account
```

### Web client

Open **`http://localhost:4001/`** in a browser and click through to the web
client, or go straight to **`http://localhost:4001/webclient/`**. The web
client carries the project's theming (a dark-parchment palette — near-black
background, tan text, dark-red accent, gold links;
`mudgame/web/static/webclient/css/theme.css`) and the same MOTD. Log in or
create an account with the same `connect` / `create` flow.

> **Remote hosts.** The ports above bind for local play out of the box. If you
> are running the server on a remote machine, replace `localhost` with the
> server's hostname/IP and ensure ports 4000–4002 are reachable through any
> firewall. Production hardening (TLS, reverse proxy, port exposure) is beyond
> this quick-start.

---

## 7. First steps in the world

Once logged in, your character spawns at the **recall point — the Inner Bailey
of the Keep**. From there a new character can explore the Keep, visit the
provisioner to equip, hire henchmen at the tavern, rest to memorise spells, and
travel out to the Wilderness and the Caves of Chaos. Type `help` for the
command list and `look` to redisplay your surroundings.

---

## 8. Re-populating an existing database

Because `at_initial_setup()` only runs on the *first* boot, you cannot rely on
it to refresh the world on a database that already exists (for example after a
code update that adds content, or if the first build failed). `build_all()` is
**idempotent end to end** — it updates rooms/exits/NPCs in place and skips spawn
points that already have a live mob — so it is safe to invoke directly.

With the server **stopped** (or via the running server's admin shell), run it
from `mudgame/`:

```sh
evennia shell
```

```python
>>> from world.build.orchestrator import build_all
>>> build_all()        # idempotent: builds/populates anything missing
```

A logged-in superuser can run the same call in-game with Evennia's `py`
command:

```
py from world.build.orchestrator import build_all; build_all()
```

> **Seasonal rebuild.** The seasonal reset path (`world.build.orchestrator
> .rebuild_world()`, driven by the `season_manager`) despawns the old
> population and re-runs `build_all()` for a freshly rolled world. Player state
> — characters, XP, gear, bank, leaderboard — carries no spawn tag and is never
> touched. You do not normally call this by hand; it fires at season boundaries.

---

## 9. Troubleshooting

- **`evennia: command not found`** — your virtual environment is not active, or
  `pip install -e .` did not complete. Re-activate (`source .venv/bin/activate`)
  and reinstall.
- **Commands fail with a settings/path error** — you are not inside the
  `mudgame/` game directory. `cd mudgame` and retry.
- **World looks empty after first boot** — the one-time build hook may have
  failed silently. Run `build_all()` as in
  [§8](#8-re-populating-an-existing-database) and check the server log
  (`server/logs/` under the `mudgame/` game dir) for the traceback.
- **Port already in use** — another process (or a previous, un-stopped server)
  holds 4000/4001/4002. `evennia stop`, or free the port, then `evennia start`.

---

## Running the Ralph Loop (not the game)

The autonomous agent loop that *built* this project is a separate workflow with
its own container-based setup. It is **not** required to run or play the game.
If that is what you want, see the
[Ralph Loop strategy & container doc](ralph-loop.md) and the root `README.md`
"Run the build loop" section.
