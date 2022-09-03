"""cog.py

Defines the cog class for the Music command category.
"""

from typing import Literal

import discord
from discord import Interaction, app_commands
from discord.ext import commands
from discord.ext.commands import Context

from ...client import MyBot
from ...exceptions import InvariantError, NotApplicableError
from ...logger import format_model, log
from ...utils import has_humans, react_either
from .config import MusicEmbed, MusicErrorEmbed
from .player import Player
from .tracks import Platform

# ==================== HELPER FUNCTIONS ==================== #


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

    log.debug(f"Successfully joined {format_model(channel)}.")
    return channel


# ==================== COG DEFINITION ==================== #


class MusicCog(commands.Cog, name="Music"):
    """Commands related to playing audio from various platforms."""

    def __init__(self, bot: MyBot) -> None:
        self.bot = bot
        """Bot instance cog is being loaded on."""
        self._players: dict[discord.Guild, Player] = {}
        """Mapping of guild to their guild-specific player instance."""

   # ==================== HELPER METHODS ==================== #

    def get_player(self, ctx: Context[MyBot]) -> Player:
        """Get the guild-specific Player, creating it if necessary.

        Args:
            ctx (Context[MyBot]) Context of invoked command.

        Raises:
            InvariantError: Function is called from a context (such as
            a DM) such that `ctx.guild` is None.

        Returns:
            Player: Instance for the caller's guild.

        Postcondition:
            If the player already exists, update its `text_channel`
            property to the caller's text channel.
        """
        guild = ctx.guild
        if guild is None:
            raise InvariantError("get_player() was called from a DM.")
        try:
            player = self._players[guild]
            player.text_channel = ctx.channel
        except KeyError:
            player = Player(ctx)
            log.debug(f"Created new instance {player!r}.")
            self._players[guild] = player
        return player

    # ==================== HOOKS AND EVENTS ==================== #

    async def cog_before_invoke(self, ctx: Context[MyBot]) -> None:
        """Assert that commands are only called in guilds.

        TODO: I don't think this works.
        """
        if ctx.guild is None:
            raise NotApplicableError(
                "Music commands are only applicable in guilds.")

    async def cog_command_error(self,
                                ctx: Context[MyBot],
                                error: Exception
                                ) -> None:
        """Cog-specific command error handler."""
        if isinstance(error, NotApplicableError):
            log.warning(f"{type(error).__name__}: {error}")
            return

    # ==================== COMMAND CALLBACKS ==================== #
    # NOTE: Because all slash commands expect a response, hybrid
    # command callbacks must all have the postcondition that it
    # responds in some way upon termination, whether it be explicitly
    # in the callback or by postcondition of a helper function, such as
    # those in a Player instance. The helper function `react_either`
    # can be used as a shortcut for responding with a traditional emoji
    # reaction on a text command and text/embed as the interaction
    # response to a slash command.

    @commands.hybrid_command(name="join", aliases=["connect"], help="Summon bot to a channel")
    @app_commands.describe(channel="Voice channel to join")
    async def join(self,
                   ctx: Context[MyBot],
                   *,
                   channel: discord.VoiceChannel | None = None  # type: ignore
                   ) -> None:
        """Connect to the requested channel, or the caller's channel.

        Args:
            ctx (Context[MyBot]): Context of invoked command.
            channel (VoiceChannel | None, optional): Voice channel to
            join. Defaults to None, in which case, attempt to use the
            voice channel the caller is currently in.
        """
        channel = await _join_channel(ctx, channel)
        if channel is None:
            return  # Failed, caller notified

        embed = MusicEmbed(f"Connected to channel {channel.mention}.")
        await react_either(ctx, reaction="👌", embed=embed)

    @commands.hybrid_command(name="pause", help="Pauses the player.")
    async def pause(self, ctx: Context[MyBot]) -> None:
        """Pause the player if it is currently playing.

        Because `VoiceClient.pause()` is idempotent, /pause is as well.
        Repeated invocations should not change the state of the voice
        client.

        Since `ctx.voice_client` is a shortcut for
        `Guild::voice_client`, this callback does not actually need to
        touch the guild player instance.
        """
        vc: discord.VoiceClient | None = ctx.voice_client  # type: ignore
        if vc is None:
            embed = MusicErrorEmbed("Player is not playing anything.")
            await react_either(ctx,
                               embed=embed,
                               reaction="❓")
        else:
            vc.pause()
            embed = MusicEmbed("Player paused.")
            await react_either(ctx,
                               embed=embed,
                               reaction="⏸️")

    @commands.hybrid_command(name="resume", help="Resumes the player.")
    async def resume(self, ctx: Context[MyBot]) -> None:
        """Resume the player if it is currently playing.

        Because `VoiceClient.resume()` is idempotent, /resume is as
        well. Repeated invocations should not change the state of the
        voice client.

        Since `ctx.voice_client` is a shortcut for
        `Guild::voice_client`, this callback does not actually need to
        touch the guild player instance.
        """
        vc: discord.VoiceClient | None = ctx.voice_client  # type: ignore
        if vc is None:
            embed = MusicErrorEmbed("Player is not playing anything.")
            await react_either(ctx,
                               embed=embed,
                               reaction="❓")
        else:
            vc.resume()
            embed = MusicEmbed("Player resumed.")
            await react_either(ctx,
                               embed=embed,
                               reaction="▶️")

    @commands.hybrid_command(name="skip", aliases=["next"], help="Skip the current track")
    async def skip(self, ctx: Context[MyBot]) -> None:
        """Skip the currently playing track.

        `VoiceClient.stop()` automatically causes the player's internal
        player loop to play the next track.

        Since `ctx.voice_client` is a shortcut for
        `Guild::voice_client`, this callback does not actually need to
        touch the guild player instance.
        """
        vc: discord.VoiceClient | None = ctx.voice_client  # type: ignore
        if vc is None:
            embed = MusicErrorEmbed("Player is not playing anything.")
            await react_either(ctx,
                               embed=embed,
                               reaction="❓")
        else:
            vc.stop()
            embed = MusicEmbed("Track skipped.")
            await react_either(ctx,
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
        """Play or queue a track from any supported platform from query.

        Args:
            ctx (Context[MyBot]): Context of invoked command.
            query (str): String to submit to platform-specific search,
            or a URL, in which case the platform is inferred.
            platform (str, optional): Name of supported platforms to
            stream from. At the moment, the choices are "YouTube",
            "Spotify", and "SoundCloud. Defaults to "YouTube".

        Raises:
            InvariantError: Unexpected arg for param platform.

        Invariants:
            - Param platform must be a valid choice.
            - The context's voice client must be initialized by the
              time player is used.
        """
        # In case API calls take too long
        if ctx.interaction:
            await ctx.interaction.response.defer(thinking=True)

        # Same checking and joining process as /join
        channel = await _join_channel(ctx, None)
        if channel is None:
            return  # Failed, caller notified

        # Resolve platform from hint
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

        # Pass to backend
        player = self.get_player(ctx)
        async with channel.typing():
            await player.play_track(ctx, query, p)


async def setup(bot: MyBot) -> None:
    """Required entry point for load_extension()."""
    await bot.add_cog(MusicCog(bot))
