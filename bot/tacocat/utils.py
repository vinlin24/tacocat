"""utils.py

Defines useful constants and helper functions.
"""

import enum
import os

from discord.ext import commands


class BotMode(enum.Enum):
    """Enum for the possible modes the bot could be running in.

    LOCAL means the bot is running from a local machine. For the most
    part, this is synonymous with DEVELOPMENT mode.
    REMOTE means the bot is running from a remote host. For the most
    part, this is synonymous with PRODUCTION mode.
    """
    LOCAL = "LOCAL"
    REMOTE = "REMOTE"


def get_absolute_path(module_path: str, relative_path: str) -> str:
    """Get the absolute path from a relative path w.r.t. a module.

    Args:
        module_path (str): The `__file__` of the module this function
        is being called from.
        relative_path (str): The relative path from the calling module
        for which an absolute path should be returned.

    Returns:
        str: The absolute path to the location referenced by
        relative_path.
    """
    return os.path.join(
        os.path.dirname(module_path), relative_path
    )


def detail_call(ctx: commands.Context) -> str:
    """Detail the context of a command call for debugging lines.

    Example string:
    vinlin#5616 @ #bot-spam @ "Taco Notes" called Basic:ping (slash).

    Args:
        ctx (commands.Context): Context of the commmand that was
        invoked.

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
    name = "<Unknown>" if ctx.command is None else ctx.command.name
    if ctx.cog is not None:
        name = f"{ctx.cog.qualified_name}:{name}"

    method = "prefix" if ctx.interaction is None else "slash"
    return f"{context} called {name} ({method})."
