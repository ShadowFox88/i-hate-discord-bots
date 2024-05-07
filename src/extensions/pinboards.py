from __future__ import annotations

import sys
import traceback
import typing

import discord
import sqlalchemy
import sqlalchemy.ext.asyncio as async_sqlalchemy
from discord.ext import commands

from src import checks, views
from src.constants import HOME_GUILD_ID
from src.database import tables

if typing.TYPE_CHECKING:
    from src import Bot, Context


class Pinboards(commands.Cog):
    def __init__(self, bot: "Bot"):
        self.bot = bot

    # FIXME: Track older messages using raw event listener
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        # TODO: Use built-in logging instead
        if getattr(before.guild, "id", -1) != HOME_GUILD_ID:
            print("Ignoring message edit in non-home guild...")

            return

        if not (_message_was_pinned := not before.pinned and after.pinned):
            print("Ignoring message edit as message was not pinned...")

            return

        channel_ids_found = await self.bot.database.get_pinboard_channel_ids(before.channel.id)

        if not channel_ids_found:
            print("Ignoring message edit due to no linked channels...")

            return

        error_raised = False

        for id_ in channel_ids_found:
            pinboard_channel_found = self.bot.get_channel(id_)

            if not (pinboard_channel_found and isinstance(pinboard_channel_found, discord.TextChannel)):
                print(f"Ignoring channel with ID {id_}")

                continue

            try:
                await pinboard_channel_found.send(before.content)
            except Exception as error:
                if not error_raised:
                    error_raised = True

                traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

        if error_raised:
            return

        await before.unpin()

    @checks.depends_on("database")
    @commands.group()
    async def pinboards(self, context: Context):
        """
        Display all registered pinboards in the server
        """
        if context.invoked_subcommand:
            return

        view = views.Pinboards(author=context.author)
        generated_descriptions = ""

        async with async_sqlalchemy.AsyncSession(self.bot.database.driver) as session:
            result: sqlalchemy.Result[tuple[int]] = await session.execute(
                sqlalchemy.select(tables.PINBOARDS.columns.channel_id)
                .order_by(tables.PINBOARDS.columns.channel_id.asc())
                .limit(6)
            )

            for row in result.fetchall():
                generated_descriptions += f"<#{row.channel_id}>\n"

        if not generated_descriptions:
            # TODO: Create or use a third-party module that allows me to
            # reference these emojis by name and provides auto-complete instead
            # of relying on strings that could potentially be misspelled/misremembered
            generated_descriptions = (
                "\N{CROSS MARK} You do not have any pinboards registered in this server!\n"
                "\n"
                "\N{LEFT SPEECH BUBBLE}\N{VARIATION SELECTOR-16} \N{ROBOT FACE} To create one, use `pinboard add #channel`, where `#channel` is the text channel to transform into a pinboard."
            )

        embed = discord.Embed(title="\N{PUSHPIN} Pinboards", description=generated_descriptions)

        await context.send(embed=embed, view=view)

    @checks.depends_on("database")
    @pinboards.command(name="add")
    async def pinboard_add(self, context: Context, channel: discord.TextChannel):
        """
        Add a channel to register as a pinboard
        """
        await self.bot.database.create_pinboard(channel.id)
        await context.send(f"Registered {channel.mention} as a pinboard!")

    @checks.depends_on("database")
    @pinboards.command(name="link")
    async def pinboard_link(
        self, context: Context, channel_to_link: discord.TextChannel, pinboard_channel: discord.TextChannel
    ):
        """
        Assign a channel to an existing pinboard
        """
        await self.bot.database.link_channel_to_pinboard(channel_to_link.id, pinboard_channel.id)
        await context.send(f"Successfully linked {channel_to_link.mention} to the \N{PUSHPIN}{pinboard_channel.mention}")


async def setup(bot: Bot):
    await bot.add_cog(Pinboards(bot))
