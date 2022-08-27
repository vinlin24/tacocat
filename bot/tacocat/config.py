"""config.py

Contains package configuration options.

Implementation note: This module should not import any other module
within the project package. Naturally, since every other module should
be able to import from this module, it must be a root of the package's
dependency graph to prevent import deadlocks.
"""

import inspect
import logging
import os

import discord
import dotenv

# Load environment variables from .env if running locally
# Has no effect when running remotely with no .env file
dotenv.load_dotenv(override=True)


# Define and expose a helper class for managing file paths
class AbsPath(str):
    """Special str subclass that represents an absolute file path."""

    def __new__(cls, relative: str) -> "AbsPath":
        """Make a special str instance representing an absolute path.

        Args:
            relative (str): Relative path from the directory of the
            calling module.

        Returns:
            AbsPath: The absolute path that resolves to the same
            location as the relative path.
        """
        # Get __file__ of calling module
        caller_file = inspect.stack()[1].filename
        caller_dir = os.path.dirname(caller_file)
        abs_path = os.path.join(caller_dir, relative)
        return super().__new__(cls, abs_path)


# ==================== PROJECT METADATA ==================== #

PROJECT_NAME = "tacocat"
"""Name of the project. Should be the same as bot's name."""

# ==================== DISCORD BOT ==================== #

COMMAND_PREFIX = "-"
"""Command prefix to register for text commands."""

GATEWAY_INTENTS = discord.Intents.all()
"""Discord API gateway intents."""

# ==================== LOGGING ==================== #

PROGRAM_LOG_PATH = AbsPath("../logs/bot.log")
"""Absolute path to the program log file."""

DISCORD_LOG_PATH = AbsPath("../logs/discord.log")
"""Absolute path to the discord.py log file."""

PROGRAM_LOG_FMT = "[%(asctime)s] [%(levelname)-8s] %(filename)s:%(lineno)s: %(message)s"
"""Message format for the program logger."""

PROGRAM_LOG_DATEFMT = "%Y-%m-%d %H:%M:%S"
"""Date format for the program logger."""

PROGRAM_LOG_LEVEL = logging.INFO
"""Level for program logger. Overriden when debug verbosity active."""

DISCORD_LOG_LEVEL = logging.WARNING
"""Level for discord.py logger. Overridden when debug verbosity active."""

LOG_ALERT_LEVEL = 45
"""Custom logging level for important but non-error messages.

Should not overwrite the predefined levels (0, 10, 20, 30, 40, 50).
A good value would be between ERROR (40) and CRITICAL (50), so prudent
use of the logging settings will still treat alerts as high priority.
"""

# ==================== DEVELOPER ==================== #

DEBUG_GUILD = discord.Object(id=os.environ["TEST_GUILD_ID"])
"""Guild to sync application commands to during development/testing."""

DEVELOPER_USER_ID = int(os.environ["DEVELOPER_USER_ID"])
"""My user ID. Should be used to give me full access to the bot."""

SUPERUSER_USER_IDS = {int(user_id) for user_id in
                      os.environ["SUPERUSER_USER_IDS"].split(", ")}
"""Users, IN ADDITION TO my user ID, to give full access of the bot to."""
