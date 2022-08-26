"""utils.py

Defines useful constants and helper functions.
"""

from enum import Enum, auto


class BotMode(Enum):
    """Enum for the possible modes the bot could be running in.

    LOCAL means the bot is running from a local machine. For the most
    part, this is synonymous with DEVELOPMENT mode.
    REMOTE means the bot is running from a remote host. For the most
    part, this is synonymous with PRODUCTION mode.
    """
    LOCAL = auto()
    REMOTE = auto()
