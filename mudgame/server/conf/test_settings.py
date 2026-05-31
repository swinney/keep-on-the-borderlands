r"""Settings used when the test suite boots the engine (pytest-django).

Engine tests (``tests/engine/`` and later M2+ combat-on-the-engine suites) run
under ``pytest-django`` with ``DJANGO_SETTINGS_MODULE`` pointed here. This module
is a thin shim over the real game settings (``server.conf.settings``) with the
two adjustments Evennia's own test runner makes:

* ``TEST_ENVIRONMENT = True`` — Evennia's ``DiscoverRunner`` sets this during
  ``setup_test_environment`` (see ``evennia/server/tests/testrunner.py``). It
  lets default-object lookups (e.g. ``DEFAULT_HOME = "#2"``) tolerate the flushed
  test database instead of raising ``DoesNotExist``.
* ``GAME_DIR`` resolution — Evennia derives ``GAME_DIR`` by walking *up* from the
  current working directory looking for ``server/conf/settings.py``. Under pytest
  the cwd is the repo root (``/workspace``), one level *above* the game dir, so
  the walk never finds it. We ``chdir`` into the game dir before importing the
  base settings (which is what triggers ``settings_default``'s ``GAME_DIR``
  resolution), so paths and the test DB resolve correctly.
"""

import os

# Must run before `from server.conf.settings import *` below: that import pulls
# in evennia.settings_default, which computes GAME_DIR (and the absolute paths
# derived from it) from the cwd at import time. We chdir into the game dir for
# the duration of that import, then restore the original cwd so pytest's
# `testpaths` resolution (relative to the repo root) is unaffected. The derived
# paths are already frozen as absolute values by then.
_ORIG_CWD = os.getcwd()
_GAME_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(_GAME_DIR)

from server.conf.settings import *  # noqa: E402,F401,F403

os.chdir(_ORIG_CWD)

# Mirror evennia's test runner (testrunner.py) so engine fixtures tolerate the
# flushed test database.
TEST_ENVIRONMENT = True
