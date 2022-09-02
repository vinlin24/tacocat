"""cog.py

Defines the cog class for the Music command category.
"""

import asyncio
from typing import Literal

import discord
from discord import Interaction, app_commands
from discord.ext import commands
from discord.ext.commands import Context

from ...client import MyBot
from ...exceptions import InvariantError, NotApplicableError, NotFoundError
from ...logger import log
from ...utils import detail_call, has_humans
from .config import MusicEmbed, MusicErrorEmbed
from .tracks import Platform, Track

# ==================== HELPER FUNCTIONS ==================== #
# For abstracting complex and/or repeated processes in their
# respective main processes.


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


def _format_voice_channel(channel: discord.VoiceChannel) -> str:
    """Return a logging-friendly representation of a voice channel."""
    return (f"<VoiceChannel id={channel.id}, name={channel.name!r}>"
            f"@<Guild id={channel.guild.id}, name="
            f"{channel.guild.name!r}>")


async def _join_channel(ctx: Context[MyBot],
                        channel: discord.VoiceChannel | None  # type: ignore
                        ) -> discord.VoiceChannel | None:
    """Try to join a voice channel after checking the caller's state.

    Before the bot joins the requested channel, this function will
    check, in order:
    1. The caller must already be connected to a channel or has
    specified a channel (for /join).
    2. Player must not already be in use in another voice channel of
    the same guild.

    If any of these checks fails, this function will respond
    accordingly to the command/interaction and return None.

    Args:
        ctx (Context[MyBot]): Context of the command invoked.
        channel (VoiceChannel | None): Channel the bot should try to
        join. None if bot should try to use the caller's channel
        instead.

    Returns:
        VoiceChannel | None: The voice channel the bot is not connected
        to. None if checks failed and the bot did not connect, and this
        function has already responded to the caller accordingly.
    """
    # If no channel was provided, use the caller's channel
    if channel is None:
        vs: discord.VoiceState | None = ctx.author.voice  # type: ignore
        if vs is None or vs.channel is None:
            await ctx.send(embed=MusicErrorEmbed(
                f"{ctx.author.mention}, connect to a voice channel first "
                "or choose a channel for the /join command."
            ))
            return None

        # NOTE: VoiceState::channel is hinted as VocalGuildChannel
        # This must be an exposed implementation detail because in
        # practice and in the docs, it has the type VoiceChannel
        channel: discord.VoiceChannel = vs.channel  # type: ignore

    # NOTE: Context::voice_client is hinted as VoiceProtocol (ABC)
    # But in practice and in the docs always has the type VoiceClient
    vc: discord.VoiceClient = ctx.voice_client  # type: ignore

    # Stop caller if trying to summon bot already in use elsewhere
    if (vc is not None and vc.is_connected()
            and has_humans(vc.channel)):  # type: ignore
        if channel != vc.channel:
            await ctx.send(embed=MusicErrorEmbed(
                f"{ctx.author.mention}, someone else is listening to "
                f"music in {vc.channel.mention}."
            ))
            return None

    # Otherwise join the channel, moving if already connected to one
    try:
        await channel.connect(self_deaf=True)
    except discord.ClientException:
        await channel.guild.change_voice_state(channel=channel,
                                               self_deaf=True)

    log.debug(
        f"{detail_call(ctx)} Successfully joined "
        f"{_format_voice_channel(channel)}."
    )
    return channel


async def _get_track(ctx: Context[MyBot],
                     query: str,
                     loop: asyncio.AbstractEventLoop,
                     platform: Platform
                     ) -> Track | None:
    """Get playable track and handle any errors in attempting so.

    If there is any error in obtaining the track, this function will
    handle responding to the command/interaction and then return None.

    Args:
        ctx (Context[MyBot]): Context of command invoked.
        query (str): Command input from user.
        loop (asyncio.AbstractEventLoop): Event loop to execute the
        process in. Caller should pass in the bot's event loop.
        platform (Platform): Command input from user.

    Returns:
        Track | None: The playable audio source. None if unsuccessful.
    """
    try:
        return await Track.from_query(query, loop, platform=platform)
    except NotFoundError:
        await ctx.send(embed=MusicErrorEmbed(
            f"Could not find a track with your query {query!r}."
        ))
        return None
    except ValueError:
        await ctx.send(embed=MusicErrorEmbed(
            "An error occurred while trying to find a track with your "
            f"query {query!r}. If you're searching for a SoundCloud "
            "resource, please use the URL."
        ))
        return None


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
    async def join(self,
                   ctx: Context[MyBot],
                   *,
                   channel: discord.VoiceChannel | None = None  # type: ignore
                   ) -> None:
        channel = await _join_channel(ctx, channel)
        if channel is None:
            return  # Failed, caller notified

        embed = MusicEmbed(f"Connected to channel {channel.mention}.")
        await _react_either(ctx, reaction="👌", embed=embed)

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
        # In case API calls take too long
        if ctx.interaction:
            await ctx.interaction.response.defer(thinking=True)

        # Same checking and joining process as /join
        channel = await _join_channel(ctx, None)
        if channel is None:
            return  # Failed, caller notified

        # Determine platform from hint
        # NOTE: But if query is a URL, platform will be ignored anyway
        # as part of the design of Track.from_query()
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
        src = await _get_track(ctx, query, self.bot.loop, p)
        if src is None:
            return  # Failed, caller notified

        # Play track: TEMP, DOESN'T SUPPORT QUEUE YET
        ctx.voice_client.play(src, after=lambda e: (  # type: ignore
            e and log.error(f"Player error: {e}")
        ))

        # Success, respond to interaction
        await ctx.send(embed=_make_np_embed(src))
        log.debug(
            f"Now playing {src.title!r} from {src.platform.value} "
            f"in {_format_voice_channel(channel)}."
        )


async def setup(bot: MyBot) -> None:
    """Required entry point for load_extension()."""
    await bot.add_cog(MusicCog(bot))
