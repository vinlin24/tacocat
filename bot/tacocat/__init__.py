"""__init__.py

Set up the program and expose the bot to the main process.
"""

import os

import dotenv

from .client import MyBot
from .config import set_up_logging
from .utils import BotMode

# Load environment variables from .env if running locally
# Has no effect when running remotely with no .env file
dotenv.load_dotenv(override=True)

# Reminder: environment variables are always strings
_mode_string = os.environ["BOT_MODE"].lower()
_bot_mode = BotMode.REMOTE if _mode_string == "remote" else BotMode.LOCAL
_debug_mode = os.environ["DEBUG_MODE"].lower() == "true"

# Set up logging for this program
_program_log, _discord_handler = set_up_logging(_bot_mode, _debug_mode)

# Variables to expose to main process
bot = MyBot(os.environ["BOT_VERSION"])
bot_run_kwargs = {
    "token": os.environ["BOT_TOKEN"],
    "log_handler": _discord_handler
}

_program_log.info(f"Running program in {_bot_mode}, DEBUG_MODE={_debug_mode}.")
