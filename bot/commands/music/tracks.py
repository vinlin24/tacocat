"""tracks.py

Implements the classes representing audio tracks to be played on
Discord. These objects make all the external API calls to the
streaming libraries. This module is responsible for initializing such
instances, defining their interface, and maintaining their state.
"""

import asyncio
from abc import ABCMeta, abstractmethod

import discord
import tekore
import youtube_dl

from ...exceptions import NotFoundError
from .config import (FFMPEG_OPTIONS, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET,
                     YTDL_FORMAT_OPTIONS)

# ==================== BASE CLASS ==================== #


class Track(discord.PCMVolumeTransformer, metaclass=ABCMeta):
    """Base class for audio tracks that can be played on Discord.

    The following abstract methods must be overriden:
    ```python
    (property) title: (Self) -> str
    (property) artists: (Self) -> list[str]
    (classmethod) from_query: (Type[Self], str) -> Self
    ```
    """

    def __init__(self, source_url: str) -> None:
        """Initialize the track and make it playable on Discord.

        This method should be called indirectly through the from_query
        class method.

        Args:
            source_url: Stream URL of the resource.
        """
        audiosource = discord.FFmpegPCMAudio(source_url, **FFMPEG_OPTIONS)
        super().__init__(audiosource)

    @property
    @abstractmethod
    def title(self) -> str:
        """Title of the track."""

    @property
    @abstractmethod
    def artists(self) -> list[str]:
        """List of track artists."""

    @classmethod
    @abstractmethod
    async def from_query(cls,
                         query: str,
                         loop: asyncio.AbstractEventLoop
                         ) -> "Track":
        """Asynchronously construct a track object from a query string.

        This class method must be overriden in subclasses. This is a
        separate method from __init__ because __init__ is blocking.

        Args:
            query (str): Query one would submit to search for the
            resource on its respective platform (YouTube, Spotify,
            etc.).
            loop (AbstractEventLoop): Event loop to execute query in.
            Caller should pass in the bot's event loop.

        Returns:
            Track: Initialized class instance.
        """


# ==================== GLOBAL DATA HANDLERS ==================== #


def _init_spotify_client() -> tekore.Spotify:
    """Return an initialized Spotify client instance.

    The client does not log in as any particular user, so it only has
    access to what is in the public API.
    """
    token = tekore.request_client_token(SPOTIFY_CLIENT_ID,
                                        SPOTIFY_CLIENT_SECRET)
    return tekore.Spotify(token.access_token)


ytdl = youtube_dl.YoutubeDL(YTDL_FORMAT_OPTIONS)
"""Handler for downloading data about YouTube videos."""

spotify = _init_spotify_client()
"""Handler for making Spotify API calls."""


async def _get_info_dict(query: str, loop: asyncio.AbstractEventLoop) -> dict:
    """Get youtube-dl info dict from query.

    Args:
        query (str): Query string to submit to Youtube search.
        loop (AbstractEventLoop): Bot loop to execute search in.

    Raises:
        NotFoundError: Could not get data about YouTube video.

    Returns:
        dict: youtube-dl info dict of the first video returned from
        searching the query.
    """
    # Get info dict asynchronously
    data = await loop.run_in_executor(
        None,
        lambda: ytdl.extract_info(query, download=False)
    )

    # TODO: something went wrong, not sure what causes this
    if data is None:
        raise NotFoundError(
            f"Could not get data about YouTube video with {query=}.")

    # Take first item if query returns a playlist
    if "entries" in data:
        data = data["entries"][0]

    return data


# ==================== TRACK SUBCLASSES ==================== #


class YouTubeTrack(Track):
    """Represents the audio of a YouTube video."""

    def __init__(self, title: str, uploader: str, source_url: str) -> None:
        """Intercept from_query initialization to set properties."""
        self._title = title
        self._uploader = uploader
        super().__init__(source_url)

    @property
    def title(self) -> str:
        """Title of the YouTube video."""
        return self._title

    @property
    def artists(self) -> list[str]:
        """Name of the uploader of the YouTube video, as a list."""
        return [self._uploader]

    @classmethod
    async def from_query(cls,
                         query: str,
                         loop: asyncio.AbstractEventLoop
                         ) -> "YouTubeTrack":
        """Initialize a playable YouTube track from query.

        Raises:
            NotFoundError: Could not find a Youtube video with query.
        """
        # Construct AudioSource from info dict
        data = await _get_info_dict(query, loop)
        return cls(data["title"], data["uploader"], data["url"])


class SpotifyTrack(Track):
    """Represents the audio of a Spotify track.

    As an implementation detail, uses youtube-dl under the hood to
    obtain the audio stream URL since Spotify does not provide an API
    for downloading/streaming tracks.
    """

    def __init__(self,
                 title: str,
                 artists: list[str],
                 source_url: str
                 ) -> None:
        """Intercept from_query initialization to set properties."""
        self._title = title
        self._artists = artists
        super().__init__(source_url)

    @property
    def title(self) -> str:
        """Name of the Spotify track."""
        return self._title

    @property
    def artists(self) -> list[str]:
        """Names of the artists of the Spotify track."""
        return self._artists

    @classmethod
    async def from_query(cls,
                         query: str,
                         loop: asyncio.AbstractEventLoop
                         ) -> "SpotifyTrack":
        """Initialize a playable Spotify track from query.

        Raises:
            NotFoundError: Could not find a Spotify track with query.
            NotFoundError: Could not find a Youtube video with query.
        """
        result = spotify.search(query, limit=1)
        paging: tekore.model.FullTrackPaging = result[0]

        try:
            track = paging.items[0]
        except IndexError:
            raise NotFoundError(
                f"No Spotify track could be found with {query=}.") from None

        title = track.name
        artists = [a.name for a in track.artists]

        # Get YouTube info about track
        query = title + " " + " ".join(artists)
        data = await _get_info_dict(query, loop)

        # Construct AudioSource with track attributes and stream URL
        return cls(title, artists, data["url"])


# ==================== TEST CODE ==================== #

async def _test() -> None:
    """Throwaway test code: python -m bot.commands.music.tracks"""
    query = "sgdkhkjdahsgasdkkashjkhasdkjghsakjhkljas;h;"
    track = await YouTubeTrack.from_query(query, asyncio.get_event_loop())
    print(track.title)
    print(track.artists)

if __name__ == "__main__":
    asyncio.run(_test())
