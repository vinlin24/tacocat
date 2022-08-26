"""config.py

Contains package configuration options, including logger.
"""

import logging
import os

import discord

from .utils import BotMode, get_absolute_path

# PROJECT METADATA
PROJECT_NAME = "tacocat"

# DISCORD BOT CONFIGURATION
COMMAND_PREFIX = "-"
GATEWAY_INTENTS = discord.Intents.all()

# LOGGING CONFIGURATION
PROGRAM_LOG_PATH = get_absolute_path(__file__, "../logs/bot.log")
DISCORD_LOG_PATH = get_absolute_path(__file__, "../logs/discord.log")
PROGRAM_LOG_FMT = "[%(asctime)s] [%(levelname)-8s] %(filename)s:%(lineno)s: %(message)s"
PROGRAM_LOG_DATEFMT = "%Y-%m-%d %H:%M:%S"
PROGRAM_LOG_LEVEL = logging.INFO  # Level to use if not in debug mode
DISCORD_LOG_LEVEL = logging.WARNING  # Level to use if not in debug mode


def set_up_logging(bot_mode: BotMode,
                   debug_mode: bool
                   ) -> tuple[logging.Logger, logging.FileHandler]:
    """Set up logging for this program.

    Args:
        bot_mode (BotMode): Bot mode, LOCAL or REMOTE.
        debug_mode (bool): Whether program is running in debug mode.

    Returns:
        tuple[logging.Logger, logging.FileHandler]: The first item is
        the initialized logger for the program. The second item is the
        logging handler to override the discord.py library's default.
    """
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
    # program_log is now ready for use!
    # Can be obtained in any module with logging.getLogger(PROJECT_NAME)
    program_log.debug("Program logger initialized.")

    # Separate discord.py library logging into its own log
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
