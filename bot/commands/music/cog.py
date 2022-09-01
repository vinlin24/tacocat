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
from ...utils import detail_call
from .config import MusicEmbed, MusicErrorEmbed
from .tracks import Platform, Track

# ==================== HELPER FUNCTIONS ==================== #


async def _react_either(ctx: Context[MyBot],
                        *,
                        reaction: str = "✅",
                        content: str | None = None,
                        embed: discord.Embed | None = None,
                        ) -> None:
    """Respond to a hybrid command based on how it was invoked.

    This helper is motivated by the fact that conventional reaction
    responses do not count as an Interaction response for application
    commands, so a traditional message is needed.

    Raises:
        InvariantError: Neither content nor embed was provided.

    Args:
        ctx (Context[MyBot]): Context of hybrid command.
        reaction (str, optional): Emoji to react with if command was
        invoked as a text command. Defaults to "✅".
        content (str | None, optional): Text to send if command was
        invoked as a slash command. Defaults to None.
        embed (discord.Embed | None, optional): Embed to send if
        command was invoked as a slash command. Both content and embed
        can be provided simultaneously, and at least one of the two
        must be provided. Defaults to None.
    """
    if ctx.interaction:
        if content is None and embed is None:
            raise InvariantError(
                "Either or both arguments content and embed must be "
                "provided, but both were None."
            )
        await ctx.send(content=content, embed=embed)
    else:
        await ctx.message.add_reaction(reaction)


def _make_np_embed(src: Track) -> MusicEmbed:
    """Style an embed for the "Now playing" message.

    Args:
        src (Track): Track that is now playing.

    Returns:
        MusicEmbed: The styled embed.
    """
    embed = MusicEmbed(src.title,
                       title=f"Now playing from {src.platform.value}",
                       url=src.url)
    footer_text = src.artist
    if src.collab is not None:
        footer_text += f", {src.collab}"
    embed.set_footer(text=footer_text)
    return embed


# ==================== COG DEFINITION ==================== #


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

    @commands.hybrid_command(name="join", aliases=["connect"], help="Summon bot to a channel")
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
        embed = MusicEmbed(f"Connected to channel {channel.mention}.")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="pause", help="Pauses the player.")
    async def pause(self, ctx: Context[MyBot]) -> None:
        vc: discord.VoiceClient | None = ctx.voice_client  # type: ignore
        if vc is None:
            embed = MusicErrorEmbed("Player is not playing anything.")
            await _react_either(ctx,
                                embed=embed,
                                reaction="❓")
        else:
            vc.pause()
            embed = MusicEmbed("Player paused.")
            await _react_either(ctx,
                                embed=embed,
                                reaction="⏸️")

    @commands.hybrid_command(name="resume", help="Resumes the player.")
    async def resume(self, ctx: Context[MyBot]) -> None:
        vc: discord.VoiceClient | None = ctx.voice_client  # type: ignore
        if vc is None:
            embed = MusicErrorEmbed("Player is not playing anything.")
            await _react_either(ctx,
                                embed=embed,
                                reaction="❓")
        else:
            vc.resume()
            embed = MusicEmbed("Player resumed.")
            await _react_either(ctx,
                                embed=embed,
                                reaction="▶️")

    @commands.hybrid_command(name="skip", aliases=["next"], help="Skip the current track")
    async def skip(self, ctx: Context[MyBot]) -> None:
        # TODO: finish later, this is for easier testing
        vc: discord.VoiceClient | None = ctx.voice_client  # type: ignore
        if vc is None:
            embed = MusicErrorEmbed("Player is not playing anything.")
            await _react_either(ctx,
                                embed=embed,
                                reaction="❓")
        else:
            vc.stop()
            embed = MusicEmbed("Track skipped.")
            await _react_either(ctx,
                                embed=embed,
                                reaction="⏭️")

    @commands.hybrid_command(name="play", aliases=["p"], help="Queue a track from query")
    @app_commands.describe(
        query="Query to search with (URL for SoundCloud)",
        platform="Platform to search on (Defaults to YouTube, ignored if you use a URL)"
    )
    async def play(self,
                   ctx: Context[MyBot],
                   *,
                   query: str,
                   platform: Literal["YouTube", "Spotify",
                                     "SoundCloud"] = "YouTube",
                   ) -> None:
        if ctx.interaction:
            await ctx.interaction.response.defer(thinking=True)

        # TODO: add support for joining the channel the caller is in
        # TODO: check conditions before moving to another channel

        # Determine platform from hint, but if query is a URL,
        # it'll be overridden anyway
        match (platform):
            case "YouTube":
                p = Platform.YOUTUBE
            case "Spotify":
                p = Platform.SPOTIFY
            case "SoundCloud":
                p = Platform.SOUNDCLOUD
            case _:
                raise InvariantError(f"{platform=} is not a valid choice.")

        # Obtain playable track
        try:
            src = await Track.from_query(query, self.bot.loop, platform=p)
        except NotFoundError:
            await ctx.send(embed=MusicErrorEmbed(
                f"Could not find a track with your query {query!r}."
            ))
            return
        except ValueError:
            await ctx.send(embed=MusicErrorEmbed(
                "An error occurred while trying to find a track with your "
                f"query {query!r}. If you're searching for a SoundCloud "
                "resource, please use the URL."
            ))
            return

        # Play track: TEMP, DOESN'T SUPPORT QUEUE YET
        ctx.voice_client.play(src, after=lambda e: (  # type: ignore
            e and log.error(f"Player error: {e}")
        ))

        # Respond to interaction
        await ctx.send(embed=_make_np_embed(src))


async def setup(bot: MyBot) -> None:
    """Required entry point for load_extension()."""
    await bot.add_cog(MusicCog(bot))
