from __future__ import annotations

import typing

import discord
from discord.ext import commands

from src.constants import PREFIXES

if typing.TYPE_CHECKING:
    from src import Bot, Context


class General(commands.Cog):
    def __init__(self, bot: "Bot"):
        self.bot = bot

    @commands.command(aliases=["prefixes"])
    async def prefix(self, context: "Context"):
        embed = discord.Embed(
            title="You can ping/mention me or use the prefixes from the following examples:",
            description="\n".join(f"`{prefix}help`" for prefix in PREFIXES),
        )

        await context.send(embed=embed)


async def setup(bot: "Bot"):
    await bot.add_cog(General(bot))
