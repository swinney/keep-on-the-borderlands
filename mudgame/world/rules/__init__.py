"""Pure OSE rules core.

This package holds the Old School Essentials rules math (dice, ability
modifiers, ascending-AC combat, saving throws, XP/level, morale). It is
deliberately **Evennia-free**: no module here imports ``evennia`` or
``django``, so the whole package is unit-testable without booting the server
or a database, and is type-checked under ``mypy --strict`` (ADR 0004).

Engine code (typeclasses, managers, commands) calls into this core; the core
never calls back out.
"""
