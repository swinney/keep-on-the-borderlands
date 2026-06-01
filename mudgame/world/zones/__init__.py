"""Zone packages (zones spec R1).

Each zone is a self-contained package under ``world.zones`` exposing the
standard interface (``ROOMS``, ``EXITS``, ``MOB_TEMPLATES``, ``SPAWNS``,
``NPCS`` data lists plus an idempotent ``build()`` hook). Static content is
plain Python data — no Evennia imports — so it can be validated by tests
without booting the server. Only ``build.py`` / ``builder.py`` translate data
into live objects.

See docs/specs/zones.md and docs/specs/zones/<zone>.md.
"""
