from __future__ import annotations

import typing

import discord
from discord.ext import commands

from src import checks, database

if typing.TYPE_CHECKING:
    from src import Bot, Context


class Configuration(commands.Cog):
    def __init__(self, bot: "Bot"):
        self.bot = bot

    @checks.depends_on("database")
    @commands.group(aliases=["config"])
    async def configuration(self, context: "Context"):
        """
        View the settings for various, provided features
        """
        if context.invoked_subcommand:
            return

        configuration = await database.get_configuration()
        description = f"Automatic migration mode: `{configuration.automatic_migration_mode.name}`"
        embed = discord.Embed(title="Configuration", description=description)

        await context.send(embed=embed)

    @checks.depends_on("database")
    @configuration.command(name="set")
    async def configuration_set(
        self,
        context: "Context",
        setting: typing.Literal["automatic_migration_mode"],
        value: typing.Literal["AUTOMATED", "CONFIRMATION", "MANUAL"],
    ):
        """
        Set a given setting to the given value
        """
        updating = {setting: value}

        await database.set_configuration_settings(**updating)
        await context.send(f"Set `{setting}` to `{value}`")


async def setup(bot: "Bot"):
    await bot.add_cog(Configuration(bot))
