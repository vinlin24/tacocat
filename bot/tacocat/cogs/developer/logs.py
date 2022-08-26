"""logs.py

Implementation module for the logs command group.
"""

import os

import aiofiles
import discord
from discord.app_commands import Choice
from discord.ext.commands import Context

from ... import log
from ...config import DISCORD_LOG_PATH, PROGRAM_LOG_PATH, PROJECT_NAME
from ...utils import MESSAGE_LENGTH_LIMIT

LOG_CHOICES = [
    Choice(name=PROJECT_NAME, value=PROGRAM_LOG_PATH),
    Choice(name="discord.py", value=DISCORD_LOG_PATH),
]
"""Choices for the log_choice param of view_logs.

The choice values are the absolute paths to the corresponding log file.
"""


async def send_log_content(ctx: Context, log_path: str) -> discord.Message:
    """Send the contents of a log file.

    If the contents fit within Discord's default message length limit,
    send it enclosed in code fence markup. If it exceeds the limit,
    upload the entire .log file as the message.

    Args:
        ctx (Context): Context of the requesting command.
        log_path (str): Absolute path to the log file to read.

    Returns:
        discord.Message: The sent message, if successful.
    """
    # Asychronously read contents
    async with aiofiles.open(log_path) as fp:
        content = await fp.read()

    # If length exceeds limit, upload as file
    # +10 for code fence characters and playing it safe lol
    if len(content)+10 > MESSAGE_LENGTH_LIMIT:
        file = discord.File(
            fp=log_path,
            filename=os.path.basename(log_path)
        )
        return await ctx.send(file=file)

    return await ctx.send(f"```{content}```")
