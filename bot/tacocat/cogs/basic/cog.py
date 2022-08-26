"""cog.py

Defines the cog class for the Basic command category.
"""

from discord import Interaction, app_commands
from discord.ext import commands
from discord.ext.commands import Context

from ...utils import detail_call, log


class BasicCog(commands.Cog, name="Basic"):
    """Basic sanity-check commands that every bot should have."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="ping", help="Check bot version and latency")
    async def ping(self, ctx: Context) -> None:
        log.debug(detail_call(ctx))
        v = self.bot.version  # type: ignore
        latency = round(self.bot.latency * 1000)
        content = f"**[{v}]** Yes, I'm here! Bot latency: **{latency}** ms."
        await ctx.send(content)


async def setup(bot: commands.Bot) -> None:
    """Required entry point for load_extension()."""
    await bot.add_cog(BasicCog(bot))
