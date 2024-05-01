from __future__ import annotations

import typing

import discord
import sqlalchemy
import sqlalchemy.ext.asyncio as async_sqlalchemy
from discord.ext import commands

# from src.database import tables
from src.checks import depends_on
from src.database import tables
from src.views import Pinboards

if typing.TYPE_CHECKING:
    from src import Bot, Context


class Pinboard(commands.Cog):
    def __init__(self, bot: "Bot"):
        self.bot = bot

    @commands.group()
    @depends_on("database")
    async def pinboard(self, context: Context):
        view = Pinboards(author=context.author)
        generated_descriptions = ""

        async with async_sqlalchemy.AsyncSession(self.bot.database.driver) as session:
            statement: sqlalchemy.Select[tuple[int]] = (
                sqlalchemy.select(tables.PINBOARD.columns.channel_id)
                .order_by(tables.PINBOARD.columns.channel_id.asc())
                .limit(6)
            )
            result = await session.execute(statement)

            for row in result.fetchall():
                generated_descriptions += f"{row.channel_id}\n"

        if not generated_descriptions:
            # TODO: Create or use a third-party module that allows me to
            # reference these emojis by name and provides auto-complete instead
            # of relying on strings that could potentially be misspelled/misremembered
            generated_descriptions = (
                "\N{CROSS MARK} You do not have any pinboards registered in this server!\n"
                "\n"
                "\N{LEFT SPEECH BUBBLE}\N{VARIATION SELECTOR-16} \N{ROBOT FACE} To create one, use `pinboard create #channel`, where `#channel` is the text channel to transform into a pinboard."
            )

        embed = discord.Embed(title="\N{PUSHPIN} Pinboards", description=generated_descriptions)

        await context.send(embed=embed, view=view)


async def setup(bot: Bot):
    await bot.add_cog(Pinboard(bot))
