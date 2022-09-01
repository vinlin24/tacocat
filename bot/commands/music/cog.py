"""cog.py

Defines the cog class for the Music command category.
"""

from typing import Literal

import discord
from discord import Interaction, app_commands
from discord.ext import commands
from discord.ext.commands import Context

from ...client import MyBot
from ...exceptions import InvariantError, NotApplicableError, NotFoundError
from ...logger import log
from ...utils import ErrorEmbed, detail_call
from .tracks import SoundCloudTrack, SpotifyTrack, YouTubeTrack


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

        # Respond to interaction
        await ctx.send(f"Connected to channel {channel.mention}.")

    @commands.hybrid_command(name="pause", help="Pauses the player.")
    async def pause(self, ctx: Context[MyBot]) -> None:
        vc: discord.VoiceClient | None = ctx.voice_client  # type: ignore
        if vc is None:
            if ctx.interaction:
                await ctx.send("Player is not playing anything.")
            else:
                await ctx.message.add_reaction("❓")
        else:
            vc.pause()
            if ctx.interaction:
                await ctx.send("Player paused.")
            else:
                await ctx.message.add_reaction("⏸️")

    @commands.hybrid_command(name="resume", help="Resumes the player.")
    async def resume(self, ctx: Context[MyBot]) -> None:
        vc: discord.VoiceClient | None = ctx.voice_client  # type: ignore
        if vc is None:
            if ctx.interaction:
                await ctx.send("Player is not playing anything.")
            else:
                await ctx.message.add_reaction("❓")
        else:
            vc.resume()
            if ctx.interaction:
                await ctx.send("Player resumed.")
            else:
                await ctx.message.add_reaction("▶️")

    @commands.hybrid_command(name="play", help="Queue a track from query")
    @app_commands.describe(
        platform="Platform to search on. Defaults to YouTube",
        query="Query to search with (URL for SoundCloud)"
    )
    async def play(self,
                   ctx: Context[MyBot],
                   *,
                   query: str,
                   platform: Literal["YouTube", "Spotify",
                                     "SoundCloud"] = "YouTube",
                   ) -> None:

        # TODO: add support for joining the channel the caller is in
        # TODO: check conditions before moving to another channel

        # Determine platform
        # TODO: if query is a URL, override platform arg (this also makes more
        # sense for the text command counterpart, where it always defaults to
        # YouTube)
        match (platform):
            case "YouTube":
                cls = YouTubeTrack
            case "Spotify":
                cls = SpotifyTrack
            case "SoundCloud":
                cls = SoundCloudTrack
            case _:
                raise InvariantError(f"{platform=} is not a valid choice")

        # Obtain playable track
        try:
            src = await cls.from_query(query, self.bot.loop)
        except NotFoundError:
            embed = ErrorEmbed(
                f"Could not find a track with your query {query!r}.")
            await ctx.send(embed=embed)
            return
        except ValueError:
            embed = ErrorEmbed(
                "An error occurred while trying to find a track with your "
                f"query {query!r}. If you're searching for a SoundCloud "
                "resource, please use the URL."
            )
            await ctx.send(embed=embed)
            return

        # Play track: TEMP, DOESN'T SUPPORT QUEUE YET
        ctx.voice_client.play(src, after=lambda e: (  # type: ignore
            e and log.error(f"Player error: {e}")
        ))

        # Respond to interaction
        await ctx.send(f"Now playing from {platform}: {src.title}.")


async def setup(bot: MyBot) -> None:
    """Required entry point for load_extension()."""
    await bot.add_cog(MusicCog(bot))
