"""cog.py

Defines the cog class for the Developer command category.
"""

import discord
from discord import Interaction, app_commands
from discord.app_commands import Choice
from discord.ext import commands
from discord.ext.commands import Context

from ... import BotType, log
from ...utils import detail_call
from .logs import LOG_CHOICES, send_log_content


class DeveloperCog(commands.Cog, name="Developer"):
    """Commands to help in development, not intended for general use."""

    def __init__(self, bot: BotType) -> None:
        self.bot = bot

    @commands.hybrid_command(name="logs", help="View program logs", hidden=True)
    @app_commands.rename(log_choice="log")
    @app_commands.choices(log_choice=LOG_CHOICES)
    async def view_logs(self, ctx: Context, log_choice: Choice[str]) -> None:
        log.debug(detail_call(ctx))
        await send_log_content(ctx, log_choice.value)


async def setup(bot: BotType) -> None:
    """Required entry point for load_extension()."""
    await bot.add_cog(DeveloperCog(bot))
