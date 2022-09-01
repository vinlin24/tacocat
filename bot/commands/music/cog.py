"""cog.py

Defines the cog class for the Music command category.
"""

import discord
from discord import Interaction, app_commands
from discord.ext import commands
from discord.ext.commands import Context

from ...client import MyBot
from ...exceptions import NotApplicableError
from ...logger import log
from ...utils import detail_call
from .tracks import YouTubeTrack


class MusicCog(commands.Cog, name="Music"):
    """Commands related to playing audio from various platforms."""

    def __init__(self, bot: MyBot) -> None:
        self.bot = bot

    async def cog_before_invoke(self, ctx: Context[MyBot]) -> None:
        """Assert that commands are only called in guilds."""
        if ctx.guild is None:
            raise NotApplicableError(
                "Music commands are only applicable in guilds.")

    async def cog_command_error(self,
                                ctx: Context[MyBot],
                                error: Exception
                                ) -> None:
        """Cog-specific command error handler."""
        if isinstance(error, NotApplicableError):
            log.warning(f"{type(error).__name__}: {detail_call(ctx)}")
            return

    @commands.hybrid_command(name="join", help="Summon bot to a channel")
    @app_commands.describe(channel="Voice channel to join")
    async def join(self, ctx: Context[MyBot], *, channel: discord.VoiceChannel):

        # TODO: add support for joining the channel the caller is in
        # TODO: check conditions before moving to another channel

        if ctx.voice_client is not None:
            # voice_client is hinted as VoiceProtocol (ABC)
            # But should actually always be type VoiceClient
            return await ctx.voice_client.move_to(channel)  # type: ignore
        await channel.connect(self_deaf=True)

    @commands.hybrid_command(name="play", help="Queue a track from query")
    @app_commands.describe(query="Query to search with")
    async def play(self, ctx: Context[MyBot], *, query: str) -> None:

        # TODO: add support for joining the channel the caller is in
        # TODO: check conditions before moving to another channel

        # TODO: TEMPORARY, TESTING
        src = await YouTubeTrack.from_query(query, self.bot.loop)
        ctx.voice_client.play(src, after=lambda e: (  # type: ignore
            e and log.error(f"Player error: {e}")
        ))

        await ctx.send(f"Now playing {src.title}.")


async def setup(bot: MyBot) -> None:
    """Required entry point for load_extension()."""
    await bot.add_cog(MusicCog(bot))
