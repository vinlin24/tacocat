"""player.py

Implements the guild-specific player instance that serves as the
backend for commands in the Music cog. It is principally responsible
for managing the state of the guild's queue.
"""

import asyncio

import discord
from discord.ext.commands import Context

from ...client import MyBot
from ...exceptions import InvariantError, NotFoundError
from ...logger import format_model, log
from .config import MusicEmbed, MusicErrorEmbed
from .tracks import Platform, Track

# ==================== HELPER FUNCTIONS ==================== #


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
        query (str): Command input from caller.
        loop (asyncio.AbstractEventLoop): Event loop to execute the
        process in. Caller should pass in the bot's event loop.
        platform (Platform): Command input from caller.

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


# ==================== CLASS DEFINITION ==================== #


class Player:
    """Guild-specific music player."""

    def __init__(self, bot: MyBot, guild: discord.Guild) -> None:
        self.bot = bot
        """Bot instance that player is bound to."""
        self.guild = guild
        """The guild this player belongs to."""

    def __repr__(self) -> str:
        """Log-friendly representation of a Player instance."""
        return f"<Player for {format_model(self.guild)}>"

    @property
    def vc(self) -> discord.VoiceClient:
        """The initialized voice client associated with player's guild.

        Raises:
            InvariantError: Voice client for player's guild should be
            initialized but it's None. It is the responsibility of the
            frontend callbacks to ensure that the guild's voice client
            is in the expected state before passing control.
        """
        vc: discord.VoiceClient | None = self.guild.voice_client  # type: ignore
        if vc is None:
            raise InvariantError(
                f"Attempted to use voice client of {format_model(self.guild)} "
                "when it has not been created yet."
            )
        return vc

    # ==================== COMMAND BACKENDS ==================== #

    async def play_track(self,
                         ctx: Context[MyBot],
                         query: str,
                         platform: Platform
                         ) -> None:
        """Play or queue the track to be created from query.

        Args:
            ctx (Context[MyBot]): Context of the invoked command.
            query (str): Command input from caller.
            platform (Platform): Resolved enum member from command
            input from caller.

        Precondition:
            Uses self.vc, so it must be initialized. Else, may raise
            InvariantError.

        Postcondition:
            Responds to the command/interaction.
        """
        # Get audio source
        src = await _get_track(ctx, query, self.bot.loop, platform)
        if src is None:
            return  # Failed, caller notified

        # Play track: TEMP, DOESN'T SUPPORT QUEUE YET
        self.vc.play(src, after=lambda e: (
            e and log.error(f"Player error: {e}")
        ))

        # Success, respond to interaction
        await ctx.send(embed=_make_np_embed(src))
        log.debug(
            f"Now playing {src.title!r} from {src.platform.value} "
            f"in {format_model(self.vc.channel)}."
        )
