"""cog.py

Defines the cog class for the Basic command category.
"""

# from discord import app_commands
from discord.ext import commands

from ...utils import log


class BasicCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot


async def setup(bot: commands.Bot) -> None:
    """Required entry point for load_extension()."""
    await bot.add_cog(BasicCog(bot))
