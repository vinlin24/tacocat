"""client.py

Defines the bot, handles its initialization, and registers events.
"""

import os
from datetime import datetime
from typing import Any

import discord
from discord.ext import commands
from discord.ext.commands import (CheckFailure, CommandError, CommandNotFound,
                                  Context)

from . import config
from .config import (BOT_MODE, COMMAND_PREFIX, COMMANDS_DIR_PATH, DEBUG_GUILD,
                     DEVELOPER_USER_ID, GATEWAY_INTENTS, LOG_ALERT_LEVEL,
                     BotMode, __version__)
from .exceptions import UnexpectedError
from .logger import log
from .utils import ErrorEmbed, detail_call, render_timestamp


class MyBot(commands.Bot):
    """Represents the Discord bot client to use in this program."""

    def __init__(self) -> None:
        """Initialize the bot client to use in this program."""
        # Custom properties
        self._version = __version__
        self._bot_mode = BOT_MODE

        super().__init__(
            command_prefix=commands.when_mentioned_or(COMMAND_PREFIX),
            intents=GATEWAY_INTENTS
        )

    @property
    def version(self) -> str:
        """The version string of the bot. Read-only, set at init."""
        return self._version

    @property
    def bot_mode(self) -> BotMode:
        """What mode bot is running in. Read-only, set at init."""
        return self._bot_mode

    @property
    def debug_verbose(self) -> bool:
        """If running at debug verbosity. Can be modified at runtime."""
        return config.DEBUG_VERBOSE

    @debug_verbose.setter
    def debug_verbose(self, new_mode: bool) -> None:
        config.DEBUG_VERBOSE = new_mode

    async def setup_hook(self) -> None:
        """Perfom async setup after bot login but before connection."""
        await _load_bot_extensions(self)

        # Sync commands globally if deployed (takes hours)
        # Otherwise, just sync it to the testing guild (immediate)
        if self.bot_mode == BotMode.PRODUCTION:
            guild = None
            context = "globally"
        else:
            guild = DEBUG_GUILD
            context = f"to guild with id={DEBUG_GUILD.id}"
            # Copy global commands over to testing guild
            self.tree.copy_global_to(guild=guild)

        log.debug(f"Syncing commands {context}.")
        await self.tree.sync(guild=guild)

    async def on_ready(self) -> None:
        """Event listener for when bot is finished setting up."""
        log.log(LOG_ALERT_LEVEL, "Bot is ready!")
        # Try to notify developer for more convenient testing
        if self.debug_verbose:
            timestamp = render_timestamp(datetime.now())
            content = (
                f"{timestamp}@`on_ready`: Running version **{self.version}** "
                f"in **{self.bot_mode.name}** mode."
            )
            try:
                await self.send_to_dev_dm(content)
            except UnexpectedError:
                log.exception("Could not send message to DM.")

    async def on_command_error(self, ctx: Context, exc: CommandError, /) -> None:
        """Handler for command errors."""
        # Completely ignore unrecognized text commands
        if isinstance(exc, CommandNotFound):
            return

        # TODO: check more specific types of CheckFailure here...
        # Also figure out what the equivalent is for app_commands...

        # Generic check failed usually means the caller is unauthorized
        if isinstance(exc, CheckFailure):
            log.info(f"Check failed when {detail_call(ctx)}")
            embed = ErrorEmbed("You are not allowed to run this command.")
            await ctx.send(embed=embed)
            return

        # If I missed something, be sure to let me know
        # DO NOT LET UNACCOUNTED EXCEPTIONS PASS SILENTLY
        log.critical("An unaccounted command error occurred.")
        return await super().on_command_error(ctx, exc)

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
            UnexpectedError: An unexpected error where the User object
            for the developer couldn't be found with Bot.get_user().

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
    num_success = 0
    num_total = 0

    # cogs/ should contain subdirectories for each cog implementation
    for dirname in os.listdir(COMMANDS_DIR_PATH):
        dirpath = os.path.join(COMMANDS_DIR_PATH, dirname)

        # But if there's somehow a file, warn the log
        try:
            cog_contents = os.listdir(dirpath)
        except NotADirectoryError:
            log.warning(
                "There must only be directories inside the cogs/ directory. "
                f"Found file {dirname!r} instead."
            )
            continue

        # Within each subdirectory, there should be exactly one cog.py
        for filename in cog_contents:
            if filename == "cog.py":
                num_total += 1
                name = f".commands.{dirname}.cog"
                try:
                    await bot.load_extension(name, package=__package__)
                    log.debug(f"Loaded {name=} as bot extension.")
                    num_success += 1
                except commands.ExtensionError:
                    log.exception(
                        f"Failed to load {name=} as bot extension."
                    )
                break
        else:
            log.error(
                "There must be exactly one cog.py in every cogs/ "
                f"subdirectory, but none was found in {dirname!r}."
            )

    # Status report
    if num_success == num_total:
        log.info(
            "Successfully loaded all cogs as extensions "
            f"({num_success} success/{num_total} total)."
        )
    else:
        log.critical(
            "Failed to load all cogs as extensions "
            f"({num_success} success/{num_total} total)."
        )
