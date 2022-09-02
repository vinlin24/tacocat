"""__init__.py

Set up the program and expose package namespace.
"""

# Import effect: defines the bot class
from .client import MyBot, before_invoke_hook
# Import effect: loads config variables from environment variables
from .config import (BOT_MODE, BOT_TOKEN, DEBUG_VERBOSE, PROJECT_NAME,
                     __version__)
# Import effect: sets up program logging
from .logger import discord_handler as _discord_handler
from .logger import log as _log

__all__ = (
    "bot",
    "bot_run_kwargs",
    "run_bot",
)

### PACKAGE NAMESPACE ###

bot = MyBot()
"""Configured Discord bot client instance ready to be run()."""

# Register hook
bot.before_invoke(before_invoke_hook)

bot_run_kwargs = {
    "token": BOT_TOKEN,
    "log_handler": _discord_handler
}
"""Keyword arguments to pass to bot.run()."""


# Function to expose to __main__ if package is executed
def run_bot() -> None:
    """Run the bot and enter the discord.py event loop."""
    _log.info(
        f"Running {PROJECT_NAME} in {BOT_MODE.name} mode, "
        f"DEBUG_MODE={DEBUG_VERBOSE}."
    )
    bot.run(**bot_run_kwargs)
