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

### 1.1 Install Python 3.12+, git, and a venv — per OS

**Linux.** Most current distros ship Python 3.12; older LTS releases default to
an earlier version, in which case install 3.12 alongside (the
[deadsnakes PPA](https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa) on
Ubuntu, or [`pyenv`](https://github.com/pyenv/pyenv)).

```sh
# Debian 12+ / Ubuntu 24.04+  — the default python3 IS 3.12; use `python3` below
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git

# Ubuntu 22.04 / older  — default python3 is < 3.12, so get 3.12 from deadsnakes
sudo add-apt-repository -y ppa:deadsnakes/ppa && sudo apt update
sudo apt install -y python3.12 python3.12-venv python3-pip git

# Fedora / RHEL / Rocky
sudo dnf install -y python3.12 python3-pip git

# Arch / Manjaro  (rolling — Python is already ≥ 3.12)
sudo pacman -S --needed python git
```

Evennia and scipy install from prebuilt wheels on common x86-64 / arm64 Linux,
so no compiler is needed. If pip ever falls back to building scipy from source,
add a build base first (`build-essential gfortran` on Debian/Ubuntu;
`gcc-gfortran python3-devel` on Fedora).

**macOS.** Use [Homebrew](https://brew.sh):

```sh
brew install python@3.12 git
```

Homebrew installs the interpreter as `python3.12`. Both Apple-silicon and Intel
Macs get prebuilt scipy/Evennia wheels, so no Xcode toolchain is needed for a
normal install (only if you ever build from source: `xcode-select --install`).

### 1.2 Verify Python

```sh
python3.12 --version      # prints 3.12.x
```

On Debian 12+/Ubuntu 24.04+/macOS where your default `python3` is already ≥ 3.12
(`python3 --version`), you can use `python3` (or `python`) wherever this guide
writes `python3.12`.

---

## 2. Install

Clone the repository and install it (editable) into a virtual environment. The
runtime dependencies — `evennia==6.0.0` and `scipy` — are declared in
`pyproject.toml` and pulled in automatically.

```sh
git clone https://github.com/swinney/keep-on-the-borderlands.git
cd keep-on-the-borderlands

python3.12 -m venv .venv           # or: python3 / python, if that is ≥ 3.12 (see §1.2)
source .venv/bin/activate          # macOS/Linux (Windows: .venv\Scripts\activate)

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

## Run with Compose (containerized)

Instead of the host venv path above, you can run the whole game as a container
with Compose. This is the unattended-friendly path: one declarative file, a
deterministic non-interactive first boot, and persistent state on a named volume.
It runs under **both** `podman compose` (rootless, consistent with the project's
container choice — `docs/decisions/0001-container-runtime.md` /
`0006-runtime-container-and-compose.md`) and `docker compose` (drop-in). It uses a
dedicated serving image (`Containerfile.runtime`) that ships only Evennia + the
game code — not the Ralph build-loop image.

**Prerequisites:** a container runtime with the Compose plugin — either
`podman` + `podman-compose`, or `docker` (Compose v2 is built in). No host Python
needed.

> **Podman note.** `podman compose` delegates to the docker-compose provider,
> which talks to the rootless Podman API socket. If `podman compose up` errors
> with *"failed to connect to the docker API at …/podman.sock"*, enable the socket
> once: `systemctl --user enable --now podman.socket`. (Plain `docker compose`
> needs no such step.)

### 1. Configure

From the repo root, copy the template and fill it in:

```sh
cp .env.example .env
```

Edit `.env`:

- **`SECRET_KEY`** — required. Generate a stable random value (changing it later
  invalidates logged-in sessions):
  ```sh
  python3 -c "import secrets; print(secrets.token_urlsafe(50))"
  ```
- **`DJANGO_SUPERUSER_USERNAME` / `_PASSWORD` / `_EMAIL`** — the server-owner
  account, created automatically on first boot (no interactive prompt).
- Optional `TELNET_PORT` / `WEB_PORT` / `WEBSOCKET_PORT` — override the published
  host ports (defaults 4000/4001/4002) if something else already binds them.

`.env` is gitignored — it holds secrets and is never committed.

### 2. Build and start

```sh
podman compose up -d --build      # or: docker compose up -d --build
```

First boot is automatic and needs no TTY: the entrypoint migrates the database,
creates the superuser from `.env`, runs the world build (`build_all()`, logged —
not the silent `at_initial_setup` hook), then starts Portal + Server. The build
takes a little time; the healthcheck has a grace period so the container is not
flagged unhealthy while the world populates.

Watch it come up:

```sh
podman compose logs -f          # look for "world build OK" then the start banner
podman compose ps               # STATUS becomes healthy once the build finishes
```

### 3. Connect

Same surfaces as the host path — telnet `localhost:4000`, web
`http://localhost:4001/` (adjust if you overrode the ports). Log in with the
superuser from `.env`, or `create` a new account.

### 4. Re-populate (idempotent)

The world build runs on every boot and is idempotent, so a restart self-heals a
half-built world. To force a rebuild against the running container:

```sh
podman compose exec mud evennia shell -c "from world.build.orchestrator import build_all; build_all()"
```

### 5. Stop / restart / reset

```sh
podman compose stop             # orderly shutdown (SIGTERM -> evennia stop)
podman compose start            # back up; state preserved
podman compose down             # remove the container; the named volume persists
podman compose down -v          # ALSO delete the volume -> wipes all game state
```

Durable state — characters, XP, gear, bank, leaderboard — lives in the SQLite
database on the `gamedata` named volume (mounted at `/app/data`). It survives
`down`/recreation; only `down -v` destroys it. Server logs stream to stdout (view
with `compose logs`), not the volume.

> **Postgres / TLS.** This Compose setup runs SQLite-in-volume (sufficient at the
> target 20-50 concurrent) and exposes raw ports. A Postgres service and a
> TLS-terminating reverse proxy are out of scope here; the design leaves seams for
> both (see the `game-deployment` change under `openspec/`).

---

## Running the Ralph Loop (not the game)

The autonomous agent loop that *built* this project is a separate workflow with
its own container-based setup. It is **not** required to run or play the game.
If that is what you want, see the
[Ralph Loop strategy & container doc](ralph-loop.md) and the root `README.md`
"Run the build loop" section.
