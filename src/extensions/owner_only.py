from __future__ import annotations

import typing

from discord.ext import commands

from src import database

if typing.TYPE_CHECKING:
    from src import Bot, Context


ALL_COMMAND_ATTRIBUTES = {"hidden": True}


class OwnerOnly(commands.Cog, command_attrs=ALL_COMMAND_ATTRIBUTES):
    def __init__(self, bot: "Bot"):
        self.bot = bot

    @commands.command()
    async def prune(self, context: "Context"):
        """
        Drop then re-create all tables
        """
        await database.prune()
        await context.send("Pruned all databases, schemas remain intact")


async def setup(bot: "Bot"):
    await bot.add_cog(OwnerOnly(bot))
