"""test_tracks.py

Unit tester for bot/commands/music/tracks.py.

Usage from project root:
```
python -m unittest discover -s ./tests
```
Or with the run.ps1 helper script:
```
./run unittest
```
"""

import asyncio
import sys
import unittest

try:
    from bot.commands.music.tracks import Platform, Track
except ImportError as e:
    print(f"{type(e).__name__}: {e}")
    sys.exit(1)


def get_loop() -> asyncio.AbstractEventLoop:
    """Helper to return the same asyncio loop instance.

    Required to prevent RunTimeError: "... attached to a different
    loop" errors.
    """
    return asyncio.get_event_loop()


class TestTracks(unittest.IsolatedAsyncioTestCase):
    async def test_youtube_search_explicit(self) -> None:
        track = await Track.from_query("never gonna give you up", get_loop(), Platform.YOUTUBE)
        self.assertIs(track.platform, Platform.YOUTUBE)

    async def test_youtube_search_implicit(self) -> None:
        track = await Track.from_query("never gonna give you up", get_loop())
        self.assertIs(track.platform, Platform.YOUTUBE)

    async def test_spotify_search(self) -> None:
        track = await Track.from_query("let her go", get_loop(), Platform.SPOTIFY)
        self.assertIs(track.platform, Platform.SPOTIFY)

    async def test_spotify_url_explicit(self) -> None:
        track = await Track.from_query("https://open.spotify.com/track/1KxwZYyzWNyZSRyErj2ojT?si=07cfd8b6a68c4ae9", get_loop(), Platform.SPOTIFY)
        self.assertIs(track.platform, Platform.SPOTIFY)

    async def test_spotify_url_implicit(self) -> None:
        track = await Track.from_query("https://open.spotify.com/track/1KxwZYyzWNyZSRyErj2ojT?si=07cfd8b6a68c4ae9", get_loop())
        self.assertIs(track.platform, Platform.SPOTIFY)

    async def test_soundcloud_url_explicit(self) -> None:
        track = await Track.from_query("https://soundcloud.com/rarinmusic/gta", get_loop(), Platform.SOUNDCLOUD)
        self.assertIs(track.platform, Platform.SOUNDCLOUD)

    async def test_soundcloud_url_implicit(self) -> None:
        track = await Track.from_query("https://soundcloud.com/rarinmusic/gta", get_loop())
        self.assertIs(track.platform, Platform.SOUNDCLOUD)

    async def test_soundcloud_search(self) -> None:
        with self.assertRaises(ValueError):
            await Track.from_query("rarinmusic gta", get_loop(), Platform.SOUNDCLOUD)


if __name__ == "__main__":
    unittest.main()
