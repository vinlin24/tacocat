"""config.py

Contains package configuration options.

Implementation NOTE: This module should not import any other module
within the project package. Naturally, since every other module should
be able to import from this module, it must be a root of the package's
dependency graph to prevent import deadlocks.
"""

import enum
import inspect
import os

import discord
import dotenv

# Load environment variables if .env file is set up
dotenv.load_dotenv(override=True)


# ==================== HELPER STRUCTURES ==================== #


class AbsPath(str):
    """Special string subclass to aid in managing file paths."""

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


class BotMode(enum.Enum):
    """Enum for the possible modes the bot could be running in."""

    DEVELOPMENT = "DEVELOPMENT"
    """This version of the bot is still being developer and/or tested.
    
    Usually, this means it is being run on my local machine.
    """

    PRODUCTION = "PRODUCTION"
    """This version of the bot is ready to be deployed on a server.
    
    Usually, this means it is being hosted on a remote service, but it
    could also be running from a dedicated computer.
    """


# ==================== PROJECT METADATA ==================== #

PROJECT_NAME = "tacocat"
"""Name of the project. Should be the same as bot's name."""

__version__ = os.environ["BOT_VERSION"]
"""Version string of the bot."""

BOT_MODE = (BotMode.PRODUCTION
            if os.environ["BOT_MODE"].lower() == "production"
            else BotMode.DEVELOPMENT)
"""Mode the bot is running in."""

DEBUG_VERBOSE = os.environ["DEBUG_VERBOSE"].lower() != "false"
"""Whether program is running at the debug verbosity setting.

This field can be set at runtime to dynamically change the program
verbosity setting.
"""


# ==================== DISCORD BOT ==================== #

BOT_TOKEN = os.environ["BOT_TOKEN"]
"""The token used to run the bot. Keep safe at all costs."""

COMMAND_PREFIX = "-"
"""Command prefix to register for text commands."""

GATEWAY_INTENTS = discord.Intents.all()
"""Discord API gateway intents."""


# ==================== FILE PATHS ==================== #

COMMANDS_DIR_PATH = AbsPath("commands/")
"""Absolute path to the commands directory, where cogs are defined."""

ASSETS_DIR_PATH = AbsPath("assets/")
"""Absolute path to the assets directory, where static files are held."""

TEMP_DIR_PATH = AbsPath("temp/")
"""Absolute path to the temp directory, where temp files are sent to."""

PROGRAM_LOG_PATH = AbsPath("logs/bot.log")
"""Absolute path to the program log file."""

DISCORD_LOG_PATH = AbsPath("logs/discord.log")
"""Absolute path to the discord.py log file."""


# ==================== LOGGING ==================== #

PROGRAM_LOG_FMT = "[%(asctime)s] [%(levelname)-8s] %(filename)s:%(lineno)s: %(message)s"
"""Message format for the program logger."""

PROGRAM_LOG_DATEFMT = "%Y-%m-%d %H:%M:%S"
"""Date format for the program logger."""

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
