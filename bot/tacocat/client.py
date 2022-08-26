"""client.py

Defines the bot, handles its initialization, and registers events.
"""

import logging
import os

from discord.ext import commands

from .config import COMMAND_PREFIX, GATEWAY_INTENTS, PROJECT_NAME
from .utils import get_absolute_path


class MyBot(commands.Bot):
    """Represents the Discord bot client to use in this program."""

    def __init__(self, version: str) -> None:
        self._version = version
        self._log = logging.getLogger(PROJECT_NAME)
        super().__init__(command_prefix=COMMAND_PREFIX,
                         intents=GATEWAY_INTENTS)

    @property
    def version(self) -> str:
        """The version string of the bot."""
        return self._version

    @property
    def log(self) -> logging.Logger:
        """The program logger."""
        return self._log

    async def setup_hook(self) -> None:
        await _load_bot_extensions(self)

    async def on_ready(self) -> None:
        """Event listener for when bot is finished setting up."""
        self.log.info("Bot is ready!")


async def _load_bot_extensions(bot: MyBot) -> None:
    """Load every cog.py files within cogs/ as bot extension.

    Args:
        bot (MyBot): The bot instance.
    """
    cogs_path = get_absolute_path(__file__, "cogs/")

    num_success = 0
    num_total = 0

    # cogs/ should contain subdirectories for each cog implementation
    for dirname in os.listdir(cogs_path):
        dirpath = os.path.join(cogs_path, dirname)

        # But if there's somehow a file, warn the log
        try:
            cog_contents = os.listdir(dirpath)
        except NotADirectoryError:
            bot.log.warning(
                "There must only be directories inside the cogs/ directory. "
                f"Found file {dirname!r} instead."
            )
            continue

        # Within each subdirectory, there should be exactly one cog.py.
        num_total += 1
        for filename in cog_contents:
            if filename == "cog.py":
                name = f".cogs.{dirname}.cog"
                try:
                    await bot.load_extension(name, package=__package__)
                    bot.log.debug(f"Loaded {name=} as bot extension.")
                    num_success += 1
                except commands.ExtensionError:
                    bot.log.exception(
                        f"Failed to load {name=} as bot extension."
                    )

        # Status report
        if num_success == num_total:
            bot.log.info(
                "Successfully loaded all cogs as extensions "
                f"({num_success} success/{num_total} total)."
            )
        else:
            bot.log.critical(
                "Failed to load all cogs as extensions "
                f"({num_success} success/{num_total} total)."
            )
