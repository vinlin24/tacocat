"""tracks.py

Implements the Track class, which represents an audio track to be
played on Discord. These objects make all the external API calls to the
streaming libraries. This module is responsible for initializing such
instances, defining their interface, and maintaining their state.
"""

import asyncio
import enum
import re
from typing import Any, NoReturn

import discord
import sclib
import tekore
import youtube_dl

from ...exceptions import InvariantError, NotFoundError
from ...logger import log
from .config import (FFMPEG_OPTIONS, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET,
                     YTDL_FORMAT_OPTIONS)

# ==================== PLATFORMS ==================== #


class Platform(enum.Enum):
    """Enum for supported platforms at the moment."""
    YOUTUBE = "YouTube"
    SPOTIFY = "Spotify"
    SOUNDCLOUD = "SoundCloud"


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


# ==================== API HANDLERS ==================== #


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


# ==================== TRACK DEFINITION ==================== #


class Track:
    """Represents an audio track to be played on Discord."""

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

    def get_playable(self) -> discord.PCMVolumeTransformer:
        """Return an audio source to be passed to `VoiceClient::play`.

        Postcondition:
            Every call to this function returns a distinct audio source
            instance despite it representing the same Track. This is
            because the discord.py library runs cleanup code on the
            audio source instance when it is finished playing, setting
            it to a bad state, unavailable for reuse.
        """
        audiosource = discord.FFmpegPCMAudio(self.stream_url,
                                             **FFMPEG_OPTIONS)
        return discord.PCMVolumeTransformer(audiosource)

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

        Raises:
            ValueError: Something other than a URL link was provided
            when platform is SoundCloud.
            NotFoundError: Failed to get a track from the query.
            InvariantError: platform is not a valid member of the
            Platform enum.

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
        log.debug(f"Running helper {func.__name__!r}...")
        return await loop.run_in_executor(None, func, query_or_url)


# ==================== HELPER FUNCTIONS ==================== #


def _infer_from_url(string: str) -> Platform | None:
    """Infer the platform from a URL pattern.

    Args:
        string (str): The string to test as a URL.

    Returns:
        Platform | None: The platform the URL corresponds to. None if
        string is not a URL or is an unrecognized pattern.
    """
    # Discord markup allows users to wrap URL in <> to suppress embeds
    string = string.lstrip("<").rstrip(">")

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


def _get_info_dict(query: str) -> dict | None:
    """Get youtube-dl info dict from query.

    This function should not raise anything. It is the responsibility
    of its caller to propagate errors. Instead, use a return value of
    None to signal failure.

    Args:
        query (str): Query string to submit to Youtube search.

    Returns:
        dict | None: youtube-dl info dict of the first video returned
        from searching the query. None if none found or there was an
        error extracting info from YouTube.
    """
    # API call
    try:
        data = ytdl.extract_info(query, download=False)
    except Exception:
        log.exception(f"Failed to extract YouTube info from {query=}")
        return None

    if data is None:
        log.warning(f"Could not get data about YouTube video with {query=}.")
        return None

    # Take first item if query returns a playlist
    if "entries" in data:
        data = data["entries"][0]

    return data


def _unpack_spotify_track(track: tekore.model.FullTrack
                          ) -> dict[str, Any] | None:
    """Prepare track attributes from a tekore Track model.

    This function should not raise anything. It is the responsibility
    of its caller to propagate errors. Instead, use a return value of
    None to signal failure.

    Args:
        track (FullTrack): tekore track model instance.

    Returns:
        dict | None: Keyword arguments that can be passed directly to
        the Track constructor to initialize a Spotify track. None if
        unpacking failed due to being unable to obtain a stream URL
        from youtube-dl.
    """
    # Unpack track attributes from Spotify database
    title = track.name
    artist = track.artists[0].name

    # If there are any more after a second artist then I'm sorry
    if len(track.artists) > 1:
        collab = track.artists[1].name
    else:
        collab = None
    url: str = track.external_urls["spotify"]

    # Get YouTube info about track using as precise a search as possible
    query = f"{title} {artist} {'' if collab is None else collab}"
    data = _get_info_dict(query)
    if data is None:
        return None  # Failed
    stream_url: str = data["url"]

    # Format as kwargs for Track constructor
    return {
        "platform": Platform.SPOTIFY,
        "title": title,
        "artist": artist,
        "collab": collab,
        "url": url,
        "stream_url": stream_url
    }


def _raise_stream_not_found(track: tekore.model.FullTrack) -> NoReturn:
    """Shortcut to call when _unpack_spotify_track returns None.

    Args:
        track (FullTrack): The offending track instance.

    Raises:
        NotFoundError: Param track failed to get a stream URL from
        youtube-dl.
    """
    raise NotFoundError(
        "Could not find a YouTube stream URL for the Spotify track with "
        f"id={track.id!r} (name={track.name!r}). Either the query did "
        "not return any results, or there was an error in extract_info()."
    )


# ==================== FACTORY FUNCTIONS ==================== #


def make_youtube_track(query_or_url: str) -> Track:
    """Construct a YouTube track instance from a query or URL.

    Args:
        query_or_url (str): Query to submit to YouTube search or a full
        YouTube video link URL.

    Raises:
        NotFoundError: Failed to extract info with youtube-dl.

    Returns:
        Track: Track instance from the YouTube platform.
    """
    # API call
    data = _get_info_dict(query_or_url)

    if data is None:
        raise NotFoundError(
            f"Could not extract any YouTube info with query {query_or_url!r}."
        )

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
    """Construct a Spotify track instance from a search query.

    Args:
        query (str): Query string to submit to Spotify search.

    Raises:
        NotFoundError: Failed to find a Spotify track with given query.
        NotFoundError: Failed to get a stream URL with youtube-dl.

    Returns:
        Track: Track instance from the Spotify platform.
    """
    # API call
    result = spotify.search(query, limit=1)
    paging: tekore.model.FullTrackPaging = result[0]

    try:
        track = paging.items[0]
    except IndexError:
        raise NotFoundError(
            f"No Spotify track could be found with {query=}.") from None

    # Construct AudioSource with track attributes and stream URL
    kwargs = _unpack_spotify_track(track) or _raise_stream_not_found(track)
    return Track(**kwargs)


def make_spotify_track_from_url(url: str) -> Track:
    """Construct a Spotify track instance from a valid track URL.

    Args:
        url (str): Full Spotify track URL.

    Raises:
        NotFoundError: Failed to get a Spotify track from URL.
        NotFoundError: Failed to get a stream URL with youtube-dl.

    Returns:
        Track: Track instance from the Spotify platform.
    """
    _, track_id = tekore.from_url(url)

    # API call
    try:
        track = spotify.track(track_id)
    except tekore.BadRequest:
        raise NotFoundError(
            f"Could not find a Spotify track with {track_id=} (obtained from "
            f"parsing {url=})."
        ) from None

    # Construct AudioSource with track attributes and stream URL
    kwargs = _unpack_spotify_track(track) or _raise_stream_not_found(track)
    return Track(**kwargs)


def make_soundcloud_track_from_url(url: str) -> Track:
    """Construct a SoundCloud track instance from a valid permalink.

    Args:
        url (str): Full SoundCloud permalink to the track.

    Raises:
        NotFoundError: Failed to get a SoundCloud track from URL.

    Returns:
        Track: Track instance from the SoundCloud platform
    """
    try:
        result = soundcloud.resolve(url)
    # Library raises this when URL cannot be resolved
    except TypeError:
        raise NotFoundError(
            f"Could not find a SoundCloud track with {url=}."
        ) from None

    # Assert that the result is a track
    if type(result) is not sclib.Track:
        log.warning(
            f"soundcloud.resolve({url=}) returns an instance of "
            f"type {type(result).__name__!r} instead of sclib.Track."
        )
        raise NotFoundError(f"Could not find a SoundCloud track with {url=}.")

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
