"""logs.py

Implementation module for the logs command.
"""

import enum
import logging
import os
import re
from typing import Callable

import discord
from discord import Interaction
from discord.app_commands import Choice

from ... import log
from ...config import (DISCORD_LOG_PATH, LOG_ALERT_LEVEL, PROGRAM_LOG_FMT,
                       PROGRAM_LOG_PATH, PROJECT_NAME)
from ...exceptions import InvariantError
from ...utils import MESSAGE_LENGTH_LIMIT

DISCORD_LOG_FMT = "[%(asctime)s] [%(levelname)-8s] %(name)s: %(message)s"
"""Message format for the discord.py library logger.

This doesn't seem to be explicitly documented anywhere, so this format
is an educated guess. It also agrees with an example found in:
https://discordpy.readthedocs.io/en/stable/logging.html
"""

# Implementation note: for some reason, the typing in the discord.py
# library causes pylance to flag the use of enum.Enums for the value of
# Choice objects. Thus, all enums used are IntEnums, which means there may be
# the extra step of resolving desired information from an integer.


class Logs(enum.IntEnum):
    """Int enum for the logs in use for this program."""
    PROJECT = enum.auto()
    DISCORD = enum.auto()


LOG_CHOICES = [
    Choice(name=PROJECT_NAME, value=Logs.PROJECT),
    Choice(name="discord.py", value=Logs.DISCORD),
]
"""Choices for the log_choice param of view_logs."""


class Constraints(enum.IntEnum):
    """General int enum for a constraint w.r.t one value."""
    ALL = enum.auto()
    AT_LEAST = enum.auto()
    AT_MOST = enum.auto()
    ABOVE = enum.auto()
    BELOW = enum.auto()
    EXACTLY = enum.auto()


FILTER_CHOICES = [
    Choice(name="At least", value=Constraints.AT_LEAST),
    Choice(name="At most", value=Constraints.AT_MOST),
    Choice(name="Above", value=Constraints.ABOVE),
    Choice(name="Below", value=Constraints.BELOW),
    Choice(name="Exactly", value=Constraints.EXACTLY),
]
"""Choices for the severity_choice param of view_logs.

The choice names correspond to how to filter the desired log levels.
"""


class LogLevels(enum.IntEnum):
    """Int enum for the logging level names available in this program."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL
    ALERT = LOG_ALERT_LEVEL


LEVEL_CHOICES = [
    Choice(name="DEBUG", value=LogLevels.DEBUG),
    Choice(name="INFO", value=LogLevels.INFO),
    Choice(name="WARNING", value=LogLevels.WARNING),
    Choice(name="ERROR", value=LogLevels.ERROR),
    Choice(name="CRITICAL", value=LogLevels.CRITICAL),
    Choice(name="ALERT", value=LogLevels.ALERT),
]
"""Choices for the level_choice param of view_logs."""


def _compile_regex(constraint_choice: int, log_level: int) -> re.Pattern:
    """Determine the regex for filtering based on the constraints.

    Args:
        constraint_choice (int): Member of the Constraints enum.
        log_level (int): Log level to compare the constraint to.

    Raises:
        InvariantError: constraint_choice is not a valid member of the
        Constraints enum.

    Returns:
        re.Pattern: The compiled pattern object.
    """
    # TODO
    # Ideally, we should parse the format string to find whether %(levelname)
    # is included at all, and then use the string to determine the regex
    # surrounding the levelname. That way, this function doesn't break when
    # new logs are added or the format of existing logs changes.
    def get_regex_from_predicate(int_method: Callable[[int, int], bool]) -> str:
        names = [member.name for member in
                 LogLevels if int_method(member.value, log_level)]
        names = "|".join(names)
        return rf"^.*\[(?:{names}) *\].*$"

    match constraint_choice:
        case Constraints.ALL:
            regex = r".*"
        case Constraints.AT_LEAST:
            regex = get_regex_from_predicate(int.__ge__)
        case Constraints.AT_MOST:
            # Get names of levels <= log_level
            regex = get_regex_from_predicate(int.__le__)
        case Constraints.ABOVE:
            regex = get_regex_from_predicate(int.__gt__)
        case Constraints.BELOW:
            regex = get_regex_from_predicate(int.__lt__)
        case Constraints.EXACTLY:
            regex = get_regex_from_predicate(int.__eq__)
        case _:
            raise InvariantError(
                f"{constraint_choice=} was not matched to a regex. Check "
                "your helper function _compile_regex and LogLevels enum."
            )

    log.debug(f"The generated regex is r\"{regex}\"")
    return re.compile(regex, re.MULTILINE)


def _get_log_path(log_choice: int) -> str:
    """Get the absolute path to the file associated with the log.

    Args:
        log_choice (int): Member of the Logs enum.

    Raises:
        InvariantError: Error caused by the given log_choice not
        mapping to ay path.

    Returns:
        str: The absolute path to the associated .log file.
    """
    match log_choice:
        case Logs.PROJECT:
            return PROGRAM_LOG_PATH
        case Logs.DISCORD:
            return DISCORD_LOG_PATH
    # This shouldn't happen but if I forget I guess
    raise InvariantError(
        f"{log_choice=} does not map to a path. Check your helper "
        "function _get_log_path and Logs enum."
    )


async def send_log_content(interaction: Interaction,
                           log_choice: int,
                           constraint_choice: int | None,
                           level_choice: int | None,
                           ephemeral: bool
                           ) -> None:
    """Send the contents of a log file.

    Backend function for the view_logs callback of the /logs command.

    If the contents fit within Discord's default message length limit,
    send it enclosed in code fence markup. If it exceeds the limit,
    upload the entire .log file as the message.

    Raises:
        InvariantError: Error caused by an implementation/maintenance
        flaw.

    Args:
        ctx (Context): Context of the requesting command.
        log_choice (int): Member of the Logs enum.
        constraint_choice (int | None): Member of the Constraints enum,
        or None.
        level_choice (int | None) Member of the LogLevels enum, or
        None.
        ephemeral (bool): Whether the message to send should be
        ephemeral.

    Returns:
        discord.Message: The sent message, if successful.
    """
    # Read contents
    log_path = _get_log_path(log_choice)
    with open(log_path, "rt") as fp:
        content = fp.read()

    if constraint_choice is not None:
        if level_choice is None:
            raise InvariantError(
                f"{constraint_choice=} was given but {level_choice=} was not."
            )
        # By design, they are the same
        log_level = level_choice

        # Redefine content to only include what is matched by pattern
        pattern = _compile_regex(constraint_choice, log_level)
        content = "\n".join(pattern.findall(content))

    # If length exceeds limit, upload as file
    # +10 for code fence characters and playing it safe lol
    if len(content)+10 > MESSAGE_LENGTH_LIMIT:
        file = discord.File(
            fp=log_path,
            filename=os.path.basename(log_path)
        )
        return await interaction.response.send_message(
            file=file, ephemeral=ephemeral)

    # If the content is empty or just whitespace
    if len(content) == 0 or content.isspace():
        return await interaction.response.send_message(
            "Nothing to send!", ephemeral=ephemeral)

    # Enclose content in code fence markup
    return await interaction.response.send_message(
        f"```{content}```", ephemeral=ephemeral)
