"""client.py

Defines the bot, handles its initialization, and registers events.
"""

import logging

from discord.ext import commands

from .config import COMMAND_PREFIX, GATEWAY_INTENTS, PROJECT_NAME


class MyBot(commands.Bot):
    """Represents the Discord bot client to use in this program."""

    def __init__(self, version: str) -> None:
        self._version = version
        self._log = logging.getLogger(PROJECT_NAME)
        super().__init__(command_prefix=COMMAND_PREFIX,
                         intents=GATEWAY_INTENTS)

    @property
    def version(self) -> str:
        """The version string of the bot."""
        return self._version

    @property
    def log(self) -> logging.Logger:
        """The program logger."""
        return self._log

    async def on_ready(self) -> None:
        """Event listener for when bot is finished setting up."""
        self.log.info("Bot is ready!")
