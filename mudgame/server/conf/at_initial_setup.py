"""
At_initial_setup module template

Custom at_initial_setup method. This allows you to hook special
modifications to the initial server startup process. Note that this
will only be run once - when the server starts up for the very first
time! It is called last in the startup process and can thus be used to
overload things that happened before it.

The module must contain a global function at_initial_setup().  This
will be called without arguments. Note that tracebacks in this module
will be QUIETLY ignored, so make sure to check it well to make sure it
does what you expect it to.

"""


def at_initial_setup():
    """Build and populate the world at first boot (world-build spec §4, §11).

    Delegates to the boot orchestrator, which is idempotent end to end, so a
    later operator-triggered rebuild on the same DB re-runs the same path safely.
    """
    from world.build.orchestrator import build_all

    build_all()
