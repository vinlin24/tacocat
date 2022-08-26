"""config.py

Contains package configuration options.
"""

import logging
import os

import discord
import dotenv

from .utils import get_absolute_path

# Load environment variables from .env if running locally
# Has no effect when running remotely with no .env file
dotenv.load_dotenv(override=True)

# ==================== PROJECT METADATA ==================== #

PROJECT_NAME = "tacocat"
"""Name of the project. Should be the same as bot's name."""

# ==================== DISCORD BOT ==================== #

COMMAND_PREFIX = "-"
"""Command prefix to register for text commands."""

GATEWAY_INTENTS = discord.Intents.all()
"""Discord API gateway intents."""

# ==================== LOGGING ==================== #

PROGRAM_LOG_PATH = get_absolute_path(__file__, "../logs/bot.log")
"""Absolute path to the program log file."""

DISCORD_LOG_PATH = get_absolute_path(__file__, "../logs/discord.log")
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

SUPERUSER_USER_IDS = [int(user_id) for user_id in
                      os.environ["SUPERUSER_USER_IDS"].split(", ")]
"""Users, IN ADDITION TO my user ID, to give full access of the bot to."""
