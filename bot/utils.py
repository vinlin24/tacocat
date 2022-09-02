"""utils.py

Defines useful constants, factories, and helper functions.
"""

import enum
from datetime import datetime
from typing import Callable

import discord
from discord import Interaction, app_commands
from discord.ext import commands

from .config import DEVELOPER_USER_ID, SUPERUSER_USER_IDS

MESSAGE_LENGTH_LIMIT = 2000
"""Default Discord message length limit in characters."""


def detail_call(ctx: commands.Context) -> str:
    """Detail the context of a text/hybrid command call for debugging.

    Example string for invoking /logs bot in the cog named Developer:
    vinlin#5616 @ #bot-spam @ "Taco Notes" called Developer::logs:bot (slash).

    This function does not support command arguments yet, but might if
    it would aid debugging.

    Args:
        ctx (commands.Context): Context of the commmand that was
        invoked. Since application-only commands pass an Interaction
        object instead of Context, this function only works with text
        or hybrid commands.

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


class TimestampFormat(enum.Enum):
    """Enum for the possible formats of a Discord rendered timestamp.

    A reference of the codes and their previews can be found here:
    https://gist.github.com/LeviSnoot/d9147767abeef2f770e9ddcd91eb85aa
    """
    DEFAULT = None
    SHORT_TIME = "t"
    LONG_TIME = "T"
    SHORT_DATE = "d"
    LONG_DATE = "D"
    SHORT_DATETIME = "f"
    LONG_DATETIME = "F"
    RELATIVE = "R"


def render_timestamp(dt: datetime,
                     format: TimestampFormat = TimestampFormat.DEFAULT
                     ) -> str:
    """Render a Discord timestamp given a datetime.

    Args:
        dt (datetime.datetime): Datetime to render. 
        format (TimestampFormat, optional): Format code to use.
        Defaults to TimestampFormat.DEFAULT, which uses Discord's
        default formatting. A reference of formats and their previews
        can be found here:
        https://gist.github.com/LeviSnoot/d9147767abeef2f770e9ddcd91eb85aa

    Returns:
        str: A string that will be rendered in Discord messages as a
        timestamp.
    """
    # Discord only accepts int
    timestamp = round(dt.timestamp())
    suffix = "" if format is TimestampFormat.DEFAULT else f":{format.value}"
    return f"<t:{timestamp}{suffix}>"


CheckDecoratorType = Callable[[app_commands.Command], app_commands.Command]
"""Type of decorators returned by app_commands.check()."""


def is_dev() -> CheckDecoratorType:
    """Register an app command to only work for the developer."""
    def predicate(interaction: Interaction) -> bool:
        return interaction.user.id == DEVELOPER_USER_ID
    return app_commands.check(predicate)


def is_superuser() -> CheckDecoratorType:
    """Register an app command to work at the superuser privilege."""
    def predicate(interaction: Interaction) -> bool:
        user_id = interaction.user.id
        return user_id == DEVELOPER_USER_ID or user_id in SUPERUSER_USER_IDS
    return app_commands.check(predicate)


# EmbedType = Literal["rich", "image", "video", "gifv", "article", "link"]
"""Allowed embed types.

Documentation:
https://discord.com/developers/docs/resources/channel#embed-object-embed-types
"""


class ErrorEmbed(discord.Embed):
    """Template embed for error messages to display on Discord."""

    def __init__(self, description: str) -> None:
        super().__init__(color=discord.Color.red(),
                         title="❌ Command Error",
                         description=description)


def has_humans(channel: discord.VoiceChannel) -> bool:
    """Whether channel currently has nonzero bots connected to it."""
    return any(not member.bot for member in channel.members)
