"""cog.py

Defines the cog class for the Basic command category.
"""

from discord import Interaction, app_commands
from discord.ext import commands
from discord.ext.commands import Context

from ...client import MyBot
from ...logger import log


class BasicCog(commands.Cog, name="Basic"):
    """Basic sanity-check commands that every bot should have."""

    def __init__(self, bot: MyBot) -> None:
        self.bot = bot
        """Bot instance cog is being loaded on."""

    @commands.hybrid_command(name="ping", help="Check bot version and latency")
    async def ping(self, ctx: Context) -> None:
        """Check bot version and latency."""
        v = self.bot.version
        latency = round(self.bot.latency * 1000)
        content = f"**[{v}]** Yes, I'm here! Bot latency: **{latency}** ms."
        await ctx.send(content)

    @app_commands.command(name="help", description="Show help message")
    async def help(self, interaction: Interaction) -> None:
        """Show help message.

        TODO: This is a placeholder command. Finish it in the future.
        """
        await interaction.response.send_message(
            "The bot doesn't seem to have a help message set up yet for "
            f"`/help`. In the meantime, use `{self.bot.command_prefix}help`.",
            ephemeral=True
        )
        return


async def setup(bot: MyBot) -> None:
    """Required entry point for load_extension()."""
    await bot.add_cog(BasicCog(bot))
