"""client.py

Defines the bot, handles its initialization, and registers events.
"""

import discord
from discord.ext import commands


class MyBot(commands.Bot):
    def __init__(self, version: str) -> None:
        self._version = version
        # todo: make this stuff configurable later
        intents = discord.Intents.all()
        super().__init__(command_prefix="-",
                         intents=intents)

    @property
    def version(self) -> str:
        """The version string of the bot."""
        return self._version

    async def on_ready(self) -> None:
        """Event listener for when bot is finished setting up."""
        print("Bot is ready!")
