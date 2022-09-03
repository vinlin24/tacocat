"""player.py

Implements the guild-specific player instance that serves as the
backend for commands in the Music cog. It is principally responsible
for managing the state of the guild's queue.
"""

import asyncio
import traceback

import discord
from discord.ext.commands import Context

from ...client import MyBot
from ...exceptions import InvariantError, NotFoundError
from ...logger import format_model, log
from ...utils import react_either
from .config import MusicEmbed, MusicErrorEmbed
from .playlists import Playlist, QueueContext
from .tracks import Platform, Track

# ==================== HELPER FUNCTIONS ==================== #


async def _get_track(ctx: Context[MyBot],
                     query: str,
                     loop: asyncio.AbstractEventLoop,
                     platform: Platform
                     ) -> Track | None:
    """Get playable track and handle any errors in attempting so.

    Args:
        ctx (Context[MyBot]): Context of command invoked.
        query (str): Command input from caller.
        loop (asyncio.AbstractEventLoop): Event loop to execute the
        process in. Caller should pass in the bot's event loop.
        platform (Platform): Command input from caller.

    Returns:
        Track | None: The playable audio source. None if unsuccessful.

    Postcondition:
        Responds to the command/interaction if there is any error in
        obtaining the track.
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


def _make_np_embed(track: Track) -> MusicEmbed:
    """Style an embed for the "Now playing" message."""
    embed = MusicEmbed(track.title,
                       title=f"Now playing from {track.platform.value}",
                       url=track.url)
    footer_text = track.artist
    if track.collab is not None:
        footer_text += f", {track.collab}"
    embed.set_footer(text=footer_text)
    return embed


def _make_queued_embed(track: Track) -> MusicEmbed:
    """Style an embed for the "Queued" message."""
    embed = MusicEmbed(track.title,
                       title=f"Queued from {track.platform.value}",
                       url=track.url)
    footer_text = track.artist
    if track.collab is not None:
        footer_text += f", {track.collab}"
    embed.set_footer(text=footer_text)
    return embed


# ==================== CLASS DEFINITION ==================== #


class Player:
    """Guild-specific music player."""

    def __init__(self, ctx: Context[MyBot]) -> None:
        """Initialize the guild-specific music player.

        Args:
            ctx (Context[MyBot]): Context of invoked command that is
            initializing the player for the first time.

        Precondition:
            ctx.guild is not None.
        """
        # Public properties
        self._bot = ctx.bot
        self._guild: discord.Guild = ctx.guild  # type: ignore
        self._text_channel = ctx.channel

        # Internal variables to manage state of guild queue
        self._queue: list[Track] = []
        """Player queue."""

        self._context: QueueContext = QueueContext.DEFAULT
        """Context of the player queue."""

        self._pos: int = 0
        """Current (zero-indexed) position in queue.

        Invariant:
            0 <= self._pos <= len(self._queue). Imagine the position as
            a cursor pointing to an index of the queue. If the position
            is the length of the queue, then that means the queue has
            been exhausted and the player loop, if active, is awaiting
            a new Track to be appended.
        """

        # NOTE: Create a task just for the typing, gets canceled immediately
        # by InvariantError in run_player_loop()
        self._loop_task = self.bot.loop.create_task(self.run_player_loop())
        """Asynchronous task to let player play tracks sequentially.

        Invariant:
            Only one such task can be active at any time.
        """

        self._np_message: discord.Message | None = None
        """The "Now playing" message to keep track of in this guild."""

    def __repr__(self) -> str:
        """Log-friendly representation of a Player instance."""
        return f"<Player for {format_model(self.guild)}>"

    # ==================== PUBLIC PROPERTIES ==================== #

    @property
    def bot(self) -> MyBot:
        """Bot instance that player is bound to."""
        return self._bot

    @property
    def guild(self) -> discord.Guild:
        """The guild this player belongs to."""
        return self._guild

    @property
    def text_channel(self) -> discord.abc.Messageable:
        """Text channel player should send messages to.

        When initialized, the Player sets it to the text channel of the
        command that created the Player. This property can be updated
        by callbacks to use the channel of the invoking command.
        """
        return self._text_channel

    @text_channel.setter
    def text_channel(self, new_channel: discord.abc.Messageable) -> None:
        self._text_channel = new_channel
        log.debug(f"{self} is now bound to {format_model(new_channel)}.")

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
            # TODO: Maybe InvariantError isn't the best description for this
            raise InvariantError(
                f"Attempted to use voice client of {format_model(self.guild)} "
                "when it has not been created yet."
            )
        return vc

    # ==================== HELPER METHODS ==================== #

    def _schedule_loop(self) -> None:
        """Schedule a new loop if `run_player_loop` is not already active.

        To be called from functions that are expected to cause the
        player to enter the loop, such as `play_track`.

        Postcondition:
            self._loop_task is unchanged if it is still running. Else,
            it is a new instance of `asyncio.Task` and automatically
            scheduled.
        """
        if self._loop_task.done():
            self._loop_task = self.bot.loop.create_task(self.run_player_loop())
            log.debug(f"Created new loop for {self}.")

    def _get_next_track(self) -> Track | None:
        """Get the next track to play and update _pos appropriately.

        Raises:
            InvariantError: _pos is not within the allowed range.

        Returns:
            Track | None: The track currently referenced by the
            internal position pointer. None if it points outside the
            queue, signifying that the queue has been exhausted.

        Postcondition:
            self._pos is updated only if a track can be returned.
        """
        if not (0 <= self._pos <= len(self._queue)):
            raise InvariantError(
                "self._pos must be at least 0 and at most len(self._queue) "
                f"== {len(self._queue)}, but it was {self._pos} instead."
            )
        try:
            track = self._queue[self._pos]
        except IndexError:
            return None
        self._pos += 1
        return track

    async def _update_np_message(self, embed: MusicEmbed | None) -> None:
        """Update the "Now playing" message in the bound text channel.

        Args:
            embed (MusicEmbed | None): Embed of the new "Now playing"
            message to send, or None to only delete the original
            message and not send any new message.
        """
        # Delete existing message if exists
        if self._np_message is not None:
            try:
                await self._np_message.delete()
            # Message already deleted by someone else
            except discord.NotFound:
                pass

        # Send and save new message
        if embed is None:
            self._np_message = None
        else:
            self._np_message = await self.text_channel.send(embed=embed)

    # ==================== PLAYER EVENT LOOP ==================== #

    async def _run_one_iteration(self) -> None:
        """Run one iteration of the player loop.

        NOTE: The main `run_player_loop` method takes care of lending
        execution. Thus, the body of this method should not attempt
        anything computation-intensive in order to prevent blocking.
        """
        # Player is already playing or is paused: don't do anything new
        if self.vc.is_playing() or self.vc.is_paused():
            return

        # Otherwise get the track pointed by current pos
        track = self._get_next_track()

        # Player is awaiting a new track: cleanup and do nothing
        if track is None:
            # Delete lingering "Now playing message"
            await self._update_np_message(None)
            return

        # Play the track
        self.vc.play(track, after=lambda e: (
            e and log.error(f"{self} play() error:\n{traceback.format_exc()}")
        ))

        # Update the "Now playing" message
        await self._update_np_message(_make_np_embed(track))
        log.info(
            f"Now playing {track.title!r} from {track.platform.value} "
            f"in {format_model(self.vc.channel)}."
        )

    async def run_player_loop(self) -> None:
        """Main loop that lets player play tracks sequentially.

        This method should be scheduled with the function
        `asyncio.create_task` to run concurrently with the main
        discord.py event loop.

        For readability, the iteration of the main loop is separated
        into its own helper method. This method thus serves as the
        driver that is responsible for handling any errors raised
        within the loop.

        Postcondition:
            This method is responsible for canceling its own task.
            When the loop terminates, self._loop_task is canceled.
        """
        try:
            while True:
                await self._run_one_iteration()
                await asyncio.sleep(0.5)  # Lend execution
        # TODO: From self.vc access, should probably make more specialized
        except InvariantError:
            log.debug(f"Guild::voice_client of {self} now None, broke loop.")
        except Exception:
            log.exception(f"Unexpected error in the loop of {self}.")
        finally:
            self._loop_task.cancel()
            log.debug(f"Player loop canceled in {self}.")
            # Delete lingering "Now playing" message
            await self._update_np_message(None)

    # ==================== COMMAND BACKENDS ==================== #

    async def after_connect(self, ctx: Context[MyBot]) -> None:
        """Code to run after the player connects via /join.

        Args:
            ctx (Context[MyBot]) Context of invoked command.

        Precondition:
            Uses self.vc, so it must be initialized. Else, raises
            InvariantError.

        Postcondition:
            Responds to the command/interaction.
        """
        # This makes the player "revive" the loop in the case of reconnecting
        self._schedule_loop()

        # Respond
        embed = MusicEmbed(f"Connected to channel {self.vc.channel.mention}.")
        await react_either(ctx, reaction="👌", embed=embed)

    async def disconnect_player(self) -> None:
        """Disconnect the player.

        Precondition:
            Uses self.vc, so it must be initialized. Else, raises
            InvariantError.

        Postcondition:
            Sets self._pos to the track that was playing before the bot
            is disconnected.
        """
        # Bring position back one track so reconnecting plays the track
        # that was previously playing
        if self._pos > 0:
            self._pos -= 1
        await self.vc.disconnect()

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
        track = await _get_track(ctx, query, self.bot.loop, platform)
        if track is None:
            return  # Failed, caller notified

        # Enqueue the track
        self._queue.append(track)
        log.info(
            f"Queued {track.title!r} from {track.platform.value} in "
            f"{format_model(ctx.guild)}."
        )

        # Enter the loop if haven't yet
        self._schedule_loop()

        # Success, respond to interaction
        await ctx.send(embed=_make_queued_embed(track))
