"""config.py

Music cog specific configuration options.
"""

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
