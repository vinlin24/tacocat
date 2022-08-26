"""cog.py

Defines the cog class for the Basic command category.
"""

from discord import Interaction, app_commands
from discord.ext import commands
from discord.ext.commands import Context

from ... import BotType, log
from ...utils import detail_call


class BasicCog(commands.Cog, name="Basic"):
    """Basic sanity-check commands that every bot should have."""

    def __init__(self, bot: BotType) -> None:
        self.bot = bot

    @commands.hybrid_command(name="ping", help="Check bot version and latency")
    async def ping(self, ctx: Context) -> None:
        log.debug(detail_call(ctx))
        v = self.bot.version
        latency = round(self.bot.latency * 1000)
        content = f"**[{v}]** Yes, I'm here! Bot latency: **{latency}** ms."
        await ctx.send(content)

    @app_commands.command(name="help", description="Show help message")
    async def help(self, interaction: Interaction) -> None:
        # temp, todo in the future
        await interaction.response.send_message(
            "The bot doesn't seem to have a help message set up yet for "
            f"`/help`. In the meantime, use `{self.bot.command_prefix}help`.",
            ephemeral=True
        )
        return


async def setup(bot: BotType) -> None:
    """Required entry point for load_extension()."""
    await bot.add_cog(BasicCog(bot))
