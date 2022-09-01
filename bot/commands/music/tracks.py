"""tracks.py

Implements the Track class, which represents a playable audio source on
Discord. These objects make all the external API calls to the
streaming libraries. This module is responsible for initializing such
instances, defining their interface, and maintaining their state.
"""

import asyncio
import enum
import re

import discord
import sclib
import tekore
import youtube_dl

from ...exceptions import InvariantError, NotFoundError
from ...logger import log
from .config import (FFMPEG_OPTIONS, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET,
                     YTDL_FORMAT_OPTIONS)


class Platform(enum.Enum):
    """Enum for supported platforms at the moment."""
    YOUTUBE = "YouTube"
    SPOTIFY = "Spotify"
    SOUNDCLOUD = "SoundCloud"


# ==================== REGEX ==================== #

# Original: https://stackoverflow.com/a/19377429/14226122
YOUTUBE_REGEX = r"^(https?:\/\/)?((www\.)?youtube\.com|youtu\.be)\/.+$"
SPOTIFY_REGEX = r"^(https?:\/\/)?open.spotify.com\/track\/[a-zA-Z0-9]+\??.+$"
# Original: https://stackoverflow.com/a/41141290/14226122
SOUNDCLOUD_REGEX = r"^(https?:\/\/)?(www.)?(m\.)?soundcloud\.com\/[\w\-\.]+(\/)+[\w\-\.]+\/?$"

youtube_pattern = re.compile(YOUTUBE_REGEX)
"""Regex finder for full-matching YouTube video URLs."""

spotify_pattern = re.compile(SPOTIFY_REGEX)
"""Regex finder for full-matching Spotify track URLs."""

soundcloud_pattern = re.compile(SOUNDCLOUD_REGEX)
"""Regex finder for full-matching SoundCloud track URLs."""


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

soundcloud = sclib.SoundcloudAPI()
"""Handler for making SoundCloud API calls."""


def _get_info_dict(query: str) -> dict:
    """Get youtube-dl info dict from query.

    Args:
        query (str): Query string to submit to Youtube search.

    Raises:
        NotFoundError: Could not get data about YouTube video.

    Returns:
        dict: youtube-dl info dict of the first video returned from
        searching the query.
    """
    data = ytdl.extract_info(query, download=False)

    if data is None:
        raise NotFoundError(
            f"Could not get data about YouTube video with {query=}.")

    # Take first item if query returns a playlist
    if "entries" in data:
        data = data["entries"][0]

    return data


def _infer_from_url(string: str) -> Platform | None:
    """Infer the platform from a URL pattern.

    Args:
        string (str): The string to test as a URL.

    Returns:
        Platform | None: The platform the URL corresponds to. None if
        string is not a URL or is an unrecognized pattern.
    """
    # These regex are mutually exclusive, so an if ladder should be fine
    if youtube_pattern.match(string):
        log.debug(f"{string=} matched YOUTUBE_REGEX.")
        return Platform.YOUTUBE
    if spotify_pattern.match(string):
        log.debug(f"{string=} matched SPOTIFY_REGEX.")
        return Platform.SPOTIFY
    if soundcloud_pattern.match(string):
        log.debug(f"{string=} matched SOUNDCLOUD_REGEX.")
        return Platform.SOUNDCLOUD

    log.debug(f"{string=} did not match any regex.")


def _unpack_spotify_track(track: tekore.model.FullTrack) -> dict:
    """Prepare track attributes from a tekore Track model.

    Args:
        track (FullTrack): tekore track model instance.

    Returns:
        dict: Keyword arguments that can be passed directly to the
        Track constructor to initialize a Spotify track.
    """
    # Unpack track attributes from Spotify database
    title = track.name
    artist = track.artists[0].name

    # If there are any more after a second artist then I'm sorry
    if len(track.artists) > 1:
        collab = track.artists[1].name
    else:
        collab = None
    url = track.external_urls["spotify"]

    # Get YouTube info about track using as precise a search as possible
    query = f"{title} {artist} {'' if collab is None else collab}"
    data = _get_info_dict(query)
    stream_url = data["url"]

    # Format as kwargs for Track constructor
    return {
        "platform": Platform.SPOTIFY,
        "title": title,
        "artist": artist,
        "collab": collab,
        "url": url,
        "stream_url": stream_url
    }


class Track(discord.PCMVolumeTransformer):
    """Represents an audio track that can be played on Discord."""

    def __init__(self,
                 platform: Platform,
                 title: str,
                 artist: str,
                 collab: str | None,
                 url: str,
                 stream_url: str
                 ) -> None:
        """Initialize a track that is playable on Discord.

        Args:
            platform (Platform): Platform this track originates from.
            As of now, the options are YOUTUBE, SPOTIFY, SOUNDCLOUD.
            title (str): Title or name of the track.
            artist (str): Name of the primary artist or uploader.
            collab (str | None): Name of the secondary artist, if any.
            url (str): Public URL link to the resource. Not to be
            confused with stream_url.
            stream_url (str): Source URL for the audio stream.
        """
        # Set properties
        self._platform = platform
        self._title = title
        self._artist = artist
        self._collab = collab
        self._url = url
        self._stream_url = stream_url

        # Construct audio source from stream URL
        audiosource = discord.FFmpegPCMAudio(stream_url, **FFMPEG_OPTIONS)
        super().__init__(audiosource)

    @property
    def platform(self) -> Platform:
        """Platform this track originates from."""
        return self._platform

    @property
    def title(self) -> str:
        """Title name of the track."""
        return self._title

    @property
    def artist(self) -> str:
        """Name of the primary artist or uploader."""
        return self._artist

    @property
    def collab(self) -> str | None:
        """Name of the secondary artist, if any."""
        return self._collab

    @property
    def url(self) -> str:
        """Link to resource. Not to be confused with stream URL."""
        return self._url

    @property
    def stream_url(self) -> str:
        """Source URL for the audio stream."""
        return self._stream_url

    @classmethod
    async def from_query(cls,
                         query_or_url: str,
                         loop: asyncio.AbstractEventLoop,
                         platform: Platform = Platform.YOUTUBE,
                         ) -> "Track":
        """Asynchronously construct a track object from a query string.

        Args:
            query_or_url (str): Query one would submit to search for
            the resource on its respective platform (YouTube, Spotify,
            etc.). Can also be a URL, in which case, the platform is
            inferred and param platform is ignored. Due to a library
            limitation at the moment, only permalink URLs are supported
            for SoundCloud tracks.
            loop (AbstractEventLoop): Event loop to execute query in.
            Caller should pass in the bot's event loop.
            platform (Platform, optional): Platform to search the query
            on. Defaults to Platform.YOUTUBE. Ignored if a valid URL is
            used, in which case, it is overriden with the appropriate
            platform.

        Returns:
            Track: Initialized class instance if successful.
        """
        # Test if input string is a recognized URL
        test = _infer_from_url(query_or_url)
        if test is not None:
            platform = test

        # Determine which helper to use based on platform and if URL used
        match (platform):

            # youtube-dl set to handle both searches and links
            case Platform.YOUTUBE:
                func = make_youtube_track

            # tekore needs to know whether to use track ID or search query
            case Platform.SPOTIFY:
                if test is None:
                    func = make_spotify_track_from_search
                else:
                    func = make_spotify_track_from_url

            # sclib needs to use permalink URL
            case Platform.SOUNDCLOUD:
                if test is None:
                    raise ValueError(
                        "Query for SoundCloud track must be a permalink URL."
                    )
                else:
                    func = make_soundcloud_track_from_url

            # If I'm dumb I guess
            case _:
                raise InvariantError(
                    "Expected a valid Platform enum member, "
                    f"got {platform!r} instead."
                )

        # Run helper asynchronously
        return await loop.run_in_executor(None, func, query_or_url)


def make_youtube_track(query_or_url: str) -> Track:
    """Construct a YouTube track instance from a query or URL."""
    # API call
    data = _get_info_dict(query_or_url)

    # Unpack attributes
    title = data["title"]
    uploader = data["uploader"]
    url = data["webpage_url"]
    stream_url = data["url"]

    # Construct AudioSource from attributes
    return Track(platform=Platform.YOUTUBE,
                 title=title,
                 artist=uploader,
                 collab=None,
                 url=url,
                 stream_url=stream_url)


def make_spotify_track_from_search(query: str) -> Track:
    """Construct a Spotify track instance from a search query."""
    # API call
    result = spotify.search(query, limit=1)
    paging: tekore.model.FullTrackPaging = result[0]

    try:
        track = paging.items[0]
    except IndexError:
        raise NotFoundError(
            f"No Spotify track could be found with {query=}.") from None

    # Construct AudioSource with track attributes and stream URL
    kwargs = _unpack_spotify_track(track)
    return Track(**kwargs)


def make_spotify_track_from_url(url: str) -> Track:
    """Construct a Spotify track instance from a valid track URL."""
    # API call
    _, track_id = tekore.from_url(url)
    track = spotify.track(track_id)

    # Construct AudioSource with track attributes and stream URL
    kwargs = _unpack_spotify_track(track)
    return Track(**kwargs)


def make_soundcloud_track_from_url(url: str) -> Track:
    """Construct a SoundCloud track instance from a valid permalink."""
    try:
        result = soundcloud.resolve(url)
    # Library raises this when URL cannot be resolved
    except TypeError:
        raise ValueError(f"Could not resolve {url=}.") from None

    # Assert that the result is a track
    if result is None:
        raise NotFoundError(
            f"Could not find any SoundCloud resource with {url=}.")
    if type(result) is not sclib.Track:
        raise ValueError(
            f"{url=} points to a playlist or other non-Track resource.")

    # Unpack track attributes from SoundCloud database
    title = result.title
    artist = result.artist
    url = result.permalink_url
    stream_url = result.get_stream_url()

    # Construct AudioSource from track attributes and stream URL
    return Track(platform=Platform.SOUNDCLOUD,
                 title=title,
                 artist=artist,
                 collab=None,
                 url=url,
                 stream_url=stream_url)


# ==================== TEST CODE ==================== #


async def _test() -> None:
    """Throwaway test code: python -m bot.commands.music.tracks"""
    soundcloud_url = "https://soundcloud.com/rarinmusic/gta"
    query = "https://open.spotify.com/track/1KxwZYyzWNyZSRyErj2ojT?si=01d847f2b4da4e49"
    track = await Track.from_query(query, asyncio.get_event_loop())
    print(track.artist)
    print(track.collab)
    print(track.title)
    print(track.url)
    print(track.stream_url)
    print(track.platform)

if __name__ == "__main__":
    asyncio.run(_test())
