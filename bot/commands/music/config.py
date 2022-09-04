"""config.py

Music cog specific configuration options.
"""

import os

import discord

from ...config import AbsPath

# ==================== COG LOGGER ==================== #

MUSIC_LOGS_DIR_PATH = AbsPath("../../logs/music/")
"""Absolute path to the logs subdirectory set aside for the Music cog."""


# ==================== AUDIO OPTIONS ==================== #

YTDL_FORMAT_OPTIONS = {
    "format": "bestaudio",
    "noplaylist": True,
    "quiet": True,
    "ignoreerrors": True,
    "default_search": "auto",
    "source_address": "0.0.0.0"  # "ipv6 addresses cause issues sometimes"
}
"""Options to use for the youtube_dl handler."""

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn"
}
"""Options to pass to discord.FFmpegPCMAudio()."""


# ==================== SPOTIFY APP CREDENTIALS ==================== #

SPOTIFY_CLIENT_ID = os.environ["SPOTIFY_CLIENT_ID"]
"""Client ID for Spotify app."""

SPOTIFY_CLIENT_SECRET = os.environ["SPOTIFY_CLIENT_SECRET"]
"""Client secret for Spotify app."""


# ==================== EMBED FACTORIES ==================== #

class MusicEmbed(discord.Embed):
    """Custom embed style for the Music cog."""

    def __init__(self,
                 description: str,
                 *,
                 title: str | None = None,
                 url: str | None = None
                 ) -> None:
        super().__init__(color=discord.Color.yellow(),
                         description=description,
                         title=title,
                         url=url)


class MusicErrorEmbed(discord.Embed):
    """Custom embed style for user errors in the Music cog."""

    def __init__(self, description: str) -> None:
        super().__init__(color=discord.Color.red(),
                         description=description)
