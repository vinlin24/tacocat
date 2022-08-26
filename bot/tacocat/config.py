"""config.py

Contains package configuration options.
"""

import logging

import discord

from .utils import get_absolute_path

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
LOG_ALERT_LEVEL = 45  # Custom logging level

# DEVELOPER CONFIGURATION
DEBUG_GUILD = discord.Object(id=874194236675866684)  # Taco Notes
