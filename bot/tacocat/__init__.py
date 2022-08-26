"""__init__.py

Set up the program and expose package namespace.
"""

import os

from .client import MyBot
from .config import PROJECT_NAME
from .logger import set_up_logging
from .utils import BotMode

__all__ = (
    "bot",
    "bot_run_kwargs",
    "log",
    "BotType",
)

### SET UP PROGRAM ###

# Reminder: environment variables are always strings
__version__ = os.environ["BOT_VERSION"]
_mode_string = os.environ["BOT_MODE"].lower()
_bot_mode = BotMode.REMOTE if _mode_string == "remote" else BotMode.LOCAL
_debug_mode = os.environ["DEBUG_MODE"].lower() == "true"

# Set up logging for this program
_program_log, _discord_handler = set_up_logging(_bot_mode, _debug_mode)

_program_log.info(
    f"Running {PROJECT_NAME} in {_bot_mode.name} mode, "
    f"DEBUG_MODE={_debug_mode}."
)

### VARIABLES TO EXPOSE ###

# For main process

bot = MyBot(version=__version__,
            bot_mode=_bot_mode,
            debug_mode=_debug_mode,
            log=_program_log)
"""Discord bot client instance."""

bot_run_kwargs = {
    "token": os.environ["BOT_TOKEN"],
    "log_handler": _discord_handler
}
"""Keyword arguments to pass to bot.run()."""

# For implementing modules

log = _program_log
"""Configured program logger.

Do NOT import this into the modules used to initialize it as they would
deadlock for obvious reasons. These include the package top-level
modules responsble for initializing the program:
- client
- config
- logger
- utils
"""

BotType = MyBot
