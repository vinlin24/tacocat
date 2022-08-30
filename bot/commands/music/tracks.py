"""tracks.py

Implements the classes representing audio tracks to be played on
Discord. These objects are all the external API calls to the
streaming libraries. This module is responsible for initializing such
instances, defining their interface, and maintaining their state.
"""

import asyncio
from abc import ABCMeta, abstractmethod

import discord
import youtube_dl

from ...exceptions import NotFoundError
from .config import FFMPEG_OPTIONS, YTDL_FORMAT_OPTIONS


class Track(discord.PCMVolumeTransformer, metaclass=ABCMeta):
    """Base class for audio tracks that can be played on Discord.

    The following abstract methods must be overriden:
    ```python
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

    @classmethod
    @abstractmethod
    async def from_query(cls,
                         query: str,
                         loop: asyncio.AbstractEventLoop
                         ) -> "Track":
        """Asynchronously construct a track object from a query string.

        This class method must be overriden in subclasses.

        Args:
            query (str): Query one would submit to search for the
            resource on its respective platform (YouTube, Spotify,
            etc.).
            loop (AbstractEventLoop): Event loop to execute query in.
            Caller should pass in the bot's event loop.

        Returns:
            Track: Initialized class instance.
        """


class YouTubeTrack(Track):
    """Represents the audio of a YouTube video."""

    ytdl = youtube_dl.YoutubeDL(YTDL_FORMAT_OPTIONS)
    """Handler for downloading data about YouTube videos."""

    def __init__(self, data: dict) -> None:
        """Intercept from_query initialization."""
        self._title = data["title"]
        super().__init__(data["url"])  # Source URL

    @property
    def title(self) -> str:
        """Title of the YouTube video."""
        return self._title

    @classmethod
    async def from_query(cls,
                         query: str,
                         loop: asyncio.AbstractEventLoop
                         ) -> "YouTubeTrack":
        # Get info dict asynchronously
        data = await loop.run_in_executor(None, lambda:
                                          cls.ytdl.extract_info(query, download=False))

        # TODO: something went wrong, not sure what causes this
        if data is None:
            raise NotFoundError(
                f"Could not get data about YouTube video with {query=}.")

        # Take first item if query returns a playlist
        if "entries" in data:
            data = data["entries"][0]

        # Construct AudioSource from info dict
        return cls(data)
