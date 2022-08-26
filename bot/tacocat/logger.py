"""logger.py

Sets up the logging for the program.
"""

import logging

from .config import (DISCORD_LOG_LEVEL, DISCORD_LOG_PATH, PROGRAM_LOG_DATEFMT,
                     PROGRAM_LOG_FMT, PROGRAM_LOG_LEVEL, PROGRAM_LOG_PATH,
                     PROJECT_NAME)
from .utils import BotMode


def set_up_logging(bot_mode: BotMode,
                   debug_mode: bool
                   ) -> tuple[logging.Logger, logging.FileHandler]:
    """Set up logging for this program.

    Args:
        bot_mode (BotMode): Bot mode, LOCAL or REMOTE.
        debug_mode (bool): Whether program is initialized at debug
        verbosity. This can be dynamically changed at runtime with the
        MyBot.debug_mode property.

    Returns:
        tuple[logging.Logger, logging.FileHandler]: The first item is
        the initialized logger for the program. The second item is the
        logging handler to override the discord.py library's default.
    """
    # Custom logging level for important but non-error messages
    logging.addLevelName(45, "ALERT")

    # Set up program logger
    program_log = logging.getLogger(PROJECT_NAME)
    file_handler = logging.FileHandler(
        filename=PROGRAM_LOG_PATH,
        mode="at" if bot_mode == BotMode.REMOTE else "wt",
        encoding="utf-8"
    )
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt=PROGRAM_LOG_FMT,
        datefmt=PROGRAM_LOG_DATEFMT
    )
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
    program_log.addHandler(file_handler)
    program_log.addHandler(stream_handler)
    program_log.setLevel(
        logging.DEBUG if debug_mode else PROGRAM_LOG_LEVEL
    )
    program_log.debug("Program logger initialized.")

    # Separate discord.py library logging into its own log file
    discord_handler = logging.FileHandler(
        filename=DISCORD_LOG_PATH,
        mode="at" if bot_mode == BotMode.REMOTE else "wt",
        encoding="utf-8"
    )
    discord_handler.setLevel(
        logging.DEBUG if debug_mode else DISCORD_LOG_LEVEL
    )
    program_log.debug("Discord log handler configured.")

    return program_log, discord_handler
