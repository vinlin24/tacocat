"""cog.py

Defines the cog class for the Basic command category.
"""

import discord
from discord import Interaction, app_commands
from discord.ext import commands
from discord.ext.commands import Context

from ...client import MyBot
from ...logger import format_model, log


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

    # TEMP: Move to Moderation cog later
    @commands.hybrid_command(name="clean",
                             aliases=["delete", "purge"],
                             description="(ADMIN) Delete most recent messages")
    @app_commands.describe(num="Number of messages to delete (between 1 and 100, defaults to 1)")
    # TODO: Some kind of privilege_or_permissions() decorator
    @commands.has_permissions(administrator=True)
    async def clean(self, ctx: Context[MyBot], *, num: int = 1) -> None:
        """Purge most recent messages in current text channel.

        Args:
            ctx (Context[MyBot]): Context of invoked command.
            num (int, optional): Number of messages to delete. This
            number should be between 1 and 100, exclusive, and defaults
            to 1.
        """
        # Assert range
        if num < 1 or num > 100:
            await ctx.send(
                "The number of messages must be between 1 and 100, inclusive",
                ephemeral=True
            )
            return

        # Delete the command message as well
        num += 1

        if ctx.interaction is not None:
            await ctx.interaction.response.defer()
        # purge() not applicable for other channel types
        if isinstance(ctx.channel, discord.TextChannel):
            # TODO: Deal with discord.Forbidden higher up somehow
            await ctx.channel.purge(limit=num)
            log.info(
                f"{ctx.author} purged {num-1} messages in "
                f"{format_model(ctx.channel)}."
            )
        else:
            await ctx.send("This command is not applicable here.",
                           ephemeral=True)
            log.warning("Attempted to use clean outside of TextChannel.")


async def setup(bot: MyBot) -> None:
    """Required entry point for load_extension()."""
    await bot.add_cog(BasicCog(bot))
