r"""
Evennia settings file.

The available options are found in the default settings file found
here:

https://www.evennia.com/docs/latest/Setup/Settings-Default.html

Remember:

Don't copy more from the default file than you actually intend to
change; this will make sure that you don't overload upstream updates
unnecessarily.

When changing a setting requiring a file system path (like
path/to/actual/file.py), use GAME_DIR and EVENNIA_DIR to reference
your game folder and the Evennia library folders respectively. Python
paths (path.to.module) should be given relative to the game's root
folder (typeclasses.foo) whereas paths within the Evennia library
needs to be given explicitly (evennia.foo).

If you want to share your game dir, including its settings, you can
put secret game- or server-specific settings in secret_settings.py.

"""

# Use the defaults from Evennia unless explicitly overridden
from evennia.settings_default import *

######################################################################
# Evennia base server config
######################################################################

# This is the name of your game. Make it catchy!
SERVERNAME = "Keep on the Borderlands"


######################################################################
# Keep on the Borderlands — project settings
######################################################################
#
# M0 intentionally keeps this section minimal so the server boots on the
# Evennia defaults. Feature configuration is wired by the milestone that
# introduces it, not speculatively here (spec-test-implement; CLAUDE.md §3):
#
#   * Contrib activation (traits, rpsystem, clothing, extended_room, xyzgrid,
#     buffs, character_creator) — added to INSTALLED_APPS / cmdsets at the
#     milestone that first uses each. Adopt-list rationale: docs/architecture.md §2.
#   * Gametime / day-night cadence (TIME_FACTOR and friends) — tuned at M11/M12,
#     where the Shrine 24h cycle and the disguised-priest "midnight act" depend
#     on it. Guessing a value here would be untested config.
#   * Global TickerHandler is on by default; combat (M2) registers tickers then.
#
# See docs/build-plan.md for the milestone order and docs/ralph-loop.md for the
# loop workflow.


######################################################################
# M8 — Wilderness / xyzgrid
######################################################################
EXTRA_LAUNCHER_COMMANDS = {
    "xyzgrid": "evennia.contrib.grid.xyzgrid.launchcmd.xyzcommand"
}
PROTOTYPE_MODULES += [  # type: ignore[name-defined]
    "evennia.contrib.grid.xyzgrid.prototypes",
]

######################################################################
# Settings given in secret_settings.py override those in this file.
######################################################################
try:
    from server.conf.secret_settings import *
except ImportError:
    print("secret_settings.py file not found or failed to import.")

######################################################################
# Containerized-runtime override (game-deployment / ADR-0006).
######################################################################
# When SECRET_KEY is provided in the environment it wins over every value above
# (including the gitignored secret_settings.py). This lets the Compose runtime
# inject a stable key from `.env` without baking it into the image, while leaving
# the host dev path unchanged: with no SECRET_KEY env var set this block is a
# no-op and secret_settings.py still supplies the key. The entrypoint is what
# *requires* the variable in the container; settings only consumes it if present.
import os as _os

_env_secret_key = _os.environ.get("SECRET_KEY")
if _env_secret_key:
    SECRET_KEY = _env_secret_key

# EVENNIA_DATA_DIR relocates the SQLite database onto a mounted volume. Evennia
# keeps the DB and conf/ both under server/, so a volume at server/ would shadow
# this settings module; pointing the DB at a sibling data dir keeps durable state
# on the volume without hiding code. Logs stream to stdout in the container (the
# entrypoint tails them), so only the DB needs a persistent path. No-op on a host
# with the variable unset.
_data_dir = _os.environ.get("EVENNIA_DATA_DIR")
if _data_dir:
    DATABASES["default"]["NAME"] = _os.path.join(_data_dir, "evennia.db3")
