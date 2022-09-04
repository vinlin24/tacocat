"""logger.py

Defines the logging for the Music cog. For the program logging to
scale, logging-intensive features such as the music commands should be
allocated to its own log file to avoid clutter and make tracing the
command history for a specific guild much easier.

Usage:
```python
from .logger import logs
log = logs[ctx.guild]  # or something like that
```
"""

import logging
import os

import discord

from ...logger import *
from .config import MUSIC_LOGS_DIR_PATH


def _set_up_guild_logger(guild: discord.Guild) -> logging.Logger:
    """Configure the guild-specific logger.

    Args:
        guild (discord.Guild): Guild of logger to configure.

    Returns:
        logging.Logger: Configured log instance.

    Precondition:
        Only called once per guild.
    """
    log_name = f"Music-{guild.id}"
    file_name = log_name + ".log"
    file_path = os.path.join(MUSIC_LOGS_DIR_PATH, file_name)
    new_log = set_up_logging(log_name, file_path)
    return new_log


class _GuildLoggers(dict):
    """Custom proxy class for guild-to-logger mapping.

    Overrides __getitem__ to return a newly configured logger instance
    instead of raising KeyError if the key is a guild for which a
    logger is not already configured.
    """

    def __getitem__(self, guild: discord.Guild) -> logging.Logger:
        new_logger = _set_up_guild_logger(guild)
        self.__setitem__(guild, new_logger)
        return new_logger


logs = _GuildLoggers()
"""Mapping of guild to guild-specific logging instances."""
