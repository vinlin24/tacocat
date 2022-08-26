"""utils.py

Defines useful constants and helper functions.
"""

import logging
import os
from enum import Enum, auto

# Program log singleton, set in config.py
log: logging.Logger = None  # type: ignore


class BotMode(Enum):
    """Enum for the possible modes the bot could be running in.

    LOCAL means the bot is running from a local machine. For the most
    part, this is synonymous with DEVELOPMENT mode.
    REMOTE means the bot is running from a remote host. For the most
    part, this is synonymous with PRODUCTION mode.
    """
    LOCAL = auto()
    REMOTE = auto()


def get_absolute_path(module_path: str, relative_path: str) -> str:
    """Get the absolute path from a relative path w.r.t a module.

    Args:
        module_path (str): The __file__ of the module this function is
        being called from.
        relative_path (str): The relative path from the calling module
        for which an absolute path should be returned.

    Returns:
        str: The absolute path to the location referenced by
        relative_path.
    """
    return os.path.join(
        os.path.dirname(module_path), relative_path
    )
