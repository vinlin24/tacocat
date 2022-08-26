"""client.py

Defines the bot, handles its initialization, and registers events.
"""

import logging
import os
from datetime import datetime
from typing import Any

import discord
from discord.ext import commands

from .config import (COMMAND_PREFIX, DEBUG_GUILD, DEVELOPER_USER_ID,
                     GATEWAY_INTENTS, LOG_ALERT_LEVEL)
from .exceptions import UnexpectedError
from .utils import BotMode, get_absolute_path, render_timestamp


class MyBot(commands.Bot):
    """Represents the Discord bot client to use in this program."""

    def __init__(self,
                 version: str,
                 bot_mode: BotMode,
                 debug_mode: bool,
                 log: logging.Logger) -> None:
        """Initialize the bot client to use in this program.

        Args:
            version (str): Bot version string.
            bot_mode (BotMode): Bot mode, LOCAL or REMOTE.
            debug_mode (bool): Program verbose option.
            log (logging.Logger): Program logger.
        """
        # Custom properties
        self._version = version
        self._bot_mode = bot_mode
        self._debug_mode = debug_mode
        self._log = log

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
        self.log.log(LOG_ALERT_LEVEL, "Bot is ready!")
        # Try to notify developer for more convenient testing
        if self.debug_mode:
            timestamp = render_timestamp(datetime.now())
            content = (
                f"{timestamp}@`on_ready`: Running version **{self.version}** "
                f"in **{self.bot_mode.name}** mode."
            )
            try:
                await self.send_to_dev_dm(content)
            except discord.DiscordException:
                self.log.exception("Could not send message to DM.")

    async def send_to_dev_dm(self,
                             content: str | None = None,
                             **send_kwargs: Any
                             ) -> discord.Message:
        """Send a message to the developer's DM channel.

        The documentation for the arguments can be found here:
        https://discordpy.readthedocs.io/en/latest/api.html#discord.DMChannel.send

        Args:
            content (str | None, optional): Content to send. Argument
            usage is the same as that in the documentation for
            DMChannel.send(). Defaults to None.
            **send_kwargs (Any): Keyword arguments identical to those
            for DMChannel.send().

        Raises:
            discord.DiscordException: An unexpected error where the
            User object for the developer couldn't be found with
            Bot.get_user().

        Returns:
            discord.Message: The message sent, if successful.
        """
        user = self.get_user(DEVELOPER_USER_ID)
        # User not found somehow
        if user is None:
            raise UnexpectedError(
                "Failed to get the User object for developer "
                f"(id={DEVELOPER_USER_ID})."
            )

        # Get the my DM, creating it if it doesn't exist yet
        dm = user.dm_channel or await user.create_dm()
        return await dm.send(content, **send_kwargs)


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
        bot.log.debug(
            "Successfully loaded all cogs as extensions "
            f"({num_success} success/{num_total} total)."
        )
    else:
        bot.log.critical(
            "Failed to load all cogs as extensions "
            f"({num_success} success/{num_total} total)."
        )
