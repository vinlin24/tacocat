"""client.py

Defines the bot, handles its initialization, and registers events.
"""

import logging
import os

from discord.ext import commands

from .config import (COMMAND_PREFIX, DEBUG_GUILD, GATEWAY_INTENTS,
                     PROJECT_NAME, BotMode)
from .utils import get_absolute_path


class MyBot(commands.Bot):
    """Represents the Discord bot client to use in this program."""

    def __init__(self, version: str, bot_mode: BotMode, debug_mode: bool) -> None:
        self._version = version
        self._bot_mode = bot_mode
        self._debug_mode = debug_mode
        # utils.log isn't set up yet at the time it's imported yet
        # You should probably rethink this initialization process
        self._log = logging.getLogger(PROJECT_NAME)
        super().__init__(command_prefix=COMMAND_PREFIX,
                         intents=GATEWAY_INTENTS)

    @property
    def version(self) -> str:
        """The version string of the bot. Read-only, set at init."""
        return self._version

    @property
    def log(self) -> logging.Logger:
        """The program logger."""
        return self._log

    @property
    def bot_mode(self) -> BotMode:
        """What mode bot is running in. Read-only, set at init."""
        return self._bot_mode

    @property
    def debug_mode(self) -> bool:
        """If running at debug verbosity. Can be modified at runtime."""
        return self._debug_mode

    @debug_mode.setter
    def debug_mode(self, new_mode: bool) -> None:
        self._debug_mode = new_mode

    async def setup_hook(self) -> None:
        """Perfom async setup after bot login but before connection."""
        await _load_bot_extensions(self)

        # Sync commands globally if running remotely (takes hours)
        # Otherwise, just sync it to the testing guild (immediate)
        if self.bot_mode == BotMode.REMOTE:
            guild = None
            context = "globally"
        else:
            guild = DEBUG_GUILD
            context = f"to guild with id={DEBUG_GUILD.id}"
            # Copy global commands over to testing guild
            self.tree.copy_global_to(guild=guild)

        self.log.debug(f"Syncing commands {context}.")
        await self.tree.sync(guild=guild)

    async def on_ready(self) -> None:
        """Event listener for when bot is finished setting up."""
        self.log.info("Bot is ready!")


async def _load_bot_extensions(bot: MyBot) -> None:
    """Load every cog.py file within cogs/ as bot extension.

    The status report (succeeded/total) only counts with respect to
    attempts to load_extension() a cog.py. If total != the number of
    subdirectories in cogs/, then that's a sign some other problem
    occurred.

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

        # Within each subdirectory, there should be exactly one cog.py
        for filename in cog_contents:
            if filename == "cog.py":
                num_total += 1
                name = f".cogs.{dirname}.cog"
                try:
                    await bot.load_extension(name, package=__package__)
                    bot.log.debug(f"Loaded {name=} as bot extension.")
                    num_success += 1
                except commands.ExtensionError:
                    bot.log.exception(
                        f"Failed to load {name=} as bot extension."
                    )
                break
        else:
            bot.log.error(
                "There must be exactly one cog.py in every cogs/ "
                f"subdirectory, but none was found in {dirname!r}."
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
