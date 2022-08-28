"""cog.py

Defines the cog class for the Developer command category.
"""

import discord
from discord import Interaction, app_commands
from discord.app_commands import Choice
from discord.ext import commands
from discord.ext.commands import Context

from ...client import MyBot
from ...logger import log
from ...utils import ErrorEmbed, detail_call, is_dev, is_superuser
from .logs_cmd import (FILTER_CHOICES, LEVEL_CHOICES, LOG_CHOICES, Constraints,
                       send_log_content)


class DeveloperCog(commands.Cog, name="Developer"):
    """Commands to help in development, not intended for general use."""

    def __init__(self, bot: MyBot) -> None:
        self.bot = bot

    @is_superuser()
    @app_commands.command(name="logs", description="(SUPER) View program logs")
    @app_commands.describe(log_choice="Log file to view",
                           filter_choice="Severity filter option",
                           level_choice="Log level to filter by",
                           show_msg="Show log for everyone to see")
    @app_commands.rename(log_choice="log",
                         filter_choice="filter",
                         level_choice="level",
                         show_msg="show")
    @app_commands.choices(log_choice=LOG_CHOICES,
                          filter_choice=FILTER_CHOICES,
                          level_choice=LEVEL_CHOICES)
    async def view_logs(self,
                        interaction: Interaction,
                        log_choice: Choice[int],
                        filter_choice: Choice[int] | None = None,
                        level_choice: Choice[int] | None = None,
                        show_msg: bool = False
                        ) -> None:
        # Evaluate defaults for optional Choices

        # If filter is not provided or it's provided without a level,
        # just don't filter at all
        if level_choice is None:
            constraint = None
            level = None

        # If level is provided without a filter, assume the user meant to
        # filter that level exactly
        elif filter_choice is None:
            constraint = Constraints.EXACTLY.value
            level = level_choice.value

        # Otherwise there's no ambiguity
        else:
            constraint = filter_choice.value
            level = level_choice.value

        # Pass to backend
        await send_log_content(interaction,
                               log_choice=log_choice.value,
                               constraint_choice=constraint,
                               level_choice=level,
                               ephemeral=not show_msg)

    @view_logs.error
    async def view_logs_error(self,
                              interaction: Interaction,
                              exc: app_commands.AppCommandError
                              ) -> None:
        if isinstance(exc, app_commands.CheckFailure):
            log.warning(
                f"Unauthorized user {interaction.user} attempted to use the "
                f"/logs command. Check failure prevented this."
            )
            embed = ErrorEmbed(
                "Only select superusers can view the program logs.")
            await interaction.response.send_message(embed=embed,
                                                    ephemeral=True)


async def setup(bot: MyBot) -> None:
    """Required entry point for load_extension()."""
    await bot.add_cog(DeveloperCog(bot))
