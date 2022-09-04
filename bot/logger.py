"""logger.py

Sets up the logging for the program. Exposes the logger as a variable
for imports as a shortcut to the boilerplate:
```python
import logging
from .config import PROJECT_NAME
log = logging.getLogger(PROJECT_NAME)
```
Usage:
```python
from .logger import log
```
"""

import logging

import discord
from discord.ext.commands import Context

from .config import (BOT_MODE, DISCORD_LOG_PATH, LOG_ALERT_LEVEL,
                     PROGRAM_LOG_DATEFMT, PROGRAM_LOG_FMT, PROGRAM_LOG_PATH,
                     PROJECT_NAME, BotMode)

# Names to include for any cogs that define their own logger.py.
__all__ = (
    "set_up_logging",
    "detail_call",
    "format_model",
)

# ==================== PROGRAM LOGGER TEMPLATE ==================== #


# Expose function so cogs can configure their own loggers.
def set_up_logging(log_name: str, file_path: str) -> logging.Logger:
    """Use program configuration to set up a specific logger.

    Args:
        log_name (str): Name of the logger to configure.
        file_path (str): Absolute path to the log file that will serve
        as the logger's file destination.

    Returns:
        logging.Logger: Configured log instance. Equivalent in memory
        to `logging.getLogger(log_name)`.
    """
    formatter = logging.Formatter(
        fmt=PROGRAM_LOG_FMT,
        datefmt=PROGRAM_LOG_DATEFMT
    )
    # All program logs will share the same stream
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    # But make the .log file separable and configurable
    file_handler = logging.FileHandler(
        filename=file_path,
        mode="at" if BOT_MODE is BotMode.PRODUCTION else "wt",
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    specific_log = logging.getLogger(log_name)
    specific_log.addHandler(file_handler)
    specific_log.addHandler(stream_handler)

    # By default, log everything
    # You can use a custom /logs or online tools to parse the log files
    specific_log.setLevel(logging.DEBUG)

    specific_log.debug(f"Logging configured for log {log_name!r}.")
    return specific_log


# ==================== PROGRAM BASE LOGGER ==================== #

# Custom logging level for important but non-error messages
logging.addLevelName(LOG_ALERT_LEVEL, "ALERT")

# Expose program logger for imports
log = set_up_logging(PROJECT_NAME, PROGRAM_LOG_PATH)
"""Program base logger."""

log.debug(f"Log {log.name!r} is the project base logger.")


# ==================== discord.py LOGGER ==================== #

# Separate discord.py library logging into its own log file
discord_handler = logging.FileHandler(
    filename=DISCORD_LOG_PATH,
    mode="at" if BOT_MODE is BotMode.PRODUCTION else "wt",
    encoding="utf-8"
)
"""Handler to override discord.py's library logging."""

discord_handler.setLevel(logging.DEBUG)
log.debug("Discord logging configured.")


# ==================== FORMATTING HELPER FUNCTIONS ==================== #


def detail_call(ctx: Context) -> str:
    """Detail the context of a text/hybrid command call for debugging.

    Example string for invoking /logs bot in the cog named Developer:
    vinlin#5616 @ #bot-spam @ "Taco Notes" called Developer::logs:bot (slash).

    This function does not support command arguments yet, but might if
    it would aid debugging.

    Args:
        ctx (Context): Context of the commmand that was invoked. Since
        application-only commands pass an Interaction object instead of
        Context, this function only works with text or hybrid commands.

    Returns:
        str: A string that can be directly passed to log.debug(). It
        details the user, channel, guild, and name and cog of called
        command to the best of ability. Also specify if the command was
        invoked by prefix or slash. See example above.
    """
    # ctx.guild is None if not available (DMs)
    guild = "<DM>" if ctx.guild is None else f"\"{ctx.guild}\""
    context = f"{ctx.author} @ #{ctx.channel} @ {guild}"

    # ctx.command can be None somehow (some app command stuff probably)
    if ctx.command is None:
        name = "<Unknown>"
    else:
        name = ctx.command.name
        # Get full name (parent groups)
        group = ctx.command.parent
        if group is not None:
            try:
                group_full: str = group.qualified_name  # type: ignore
                # Use a single : to distinguish from cog name
                name = ":".join(group_full.split()) + ":" + name
            # I don't know how this would happen
            except AttributeError:
                name = f"<Unknown>:{name}"

    if ctx.cog is not None:
        # Use a double :: to distinguish from full group name
        # This way, it's also obvious if a command is not part of any cog
        name = f"{ctx.cog.qualified_name}::{name}"

    method = "prefix" if ctx.interaction is None else "slash"
    return f"{context} called {name} ({method})."


def _format_guild(guild: discord.Guild) -> str:
    """Return a logging-friendly representation of a guild."""
    return f"<Guild id={guild.id}, name={guild.name!r}>"


def _format_voice_channel(channel: discord.VoiceChannel) -> str:
    """Return a logging-friendly representation of a voice channel."""
    return (f"<VoiceChannel id={channel.id}, name={channel.name!r}>"
            f"@{_format_guild(channel.guild)}")


def _format_text_channel(channel: discord.TextChannel) -> str:
    """Return a logging-friendly representation of a text channel."""
    return (f"<TextChannel id={channel.id}, name={channel.name!r}>"
            f"@{_format_guild(channel.guild)}")


DiscordModel = (discord.abc.Connectable | discord.abc.GuildChannel
                | discord.abc.Messageable | discord.abc.PrivateChannel
                | discord.abc.Snowflake | discord.abc.User)
"""Type hint for abstract base classes of the discord.py library."""


def format_model(model: DiscordModel | None) -> str:
    """Return log-friendly representation for certain Discord models."""
    if isinstance(model, discord.Guild):
        return _format_guild(model)
    if isinstance(model, discord.VoiceChannel):
        return _format_voice_channel(model)
    if isinstance(model, discord.TextChannel):
        return _format_text_channel(model)
    # I suppose this could be common/expected
    if model is None:
        return "<None>"
    # Undefined by this function, use its predefined __str__
    return str(model)
