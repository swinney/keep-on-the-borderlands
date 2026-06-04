# -*- coding: utf-8 -*-
"""
Connection screen

This is the text to show the user when they first connect to the game (before
they log in).

To change the login screen in this module, do one of the following:

- Define a function `connection_screen()`, taking no arguments. This will be
  called first and must return the full string to act as the connection screen.
  This can be used to produce more dynamic screens.
- Alternatively, define a string variable in the outermost scope of this module
  with the connection string that should be displayed. If more than one such
  variable is given, Evennia will pick one of them at random.

The commands available to the user when the connection screen is shown
are defined in evennia.default_cmds.UnloggedinCmdSet. The parsing and display
of the screen is done by the unlogged-in "look" command.

"""

from django.conf import settings


CONNECTION_SCREEN = """
|b==============================================================|n
       |y Keep on the Borderlands |n — |rOpen Beta|n
|b==============================================================|n

  |gKeep on the Borderlands|n is a persistent multiplayer MUD set in
  the classic B2 adventure module (Old School Essentials rules).

  Connect via telnet or the web client at the address above.

  |wconnect <username> <password>|n  — log in to an existing account
  |wcreate <username> <password>|n   — create a new account

  Type |whelp|n for a list of commands.
  Type |wlook|n to redisplay this screen.

  Server: |g{}|n
|b==============================================================|n""".format(
    settings.SERVERNAME
)
