"""playlists.py

Implements the Playlist class to represent ordered collections of
Tracks. This module handles maintaining its state and defining
operations such as loading and saving them to an external database.
"""

import enum


class QueueContext(enum.Enum):
    """Enum for possible contexts to describe a queue or playlist."""

    DEFAULT = enum.auto()
    """Specifies a collection of Tracks from any platform."""

    YOUTUBE = enum.auto()
    """Specifies a YouTube playlist."""

    SPOTIFY = enum.auto()
    """Specifies a Spotify playlist."""

    SOUNDCLOUD = enum.auto()
    """Specifies a SoundCloud playlist."""


class Playlist:
    pass
