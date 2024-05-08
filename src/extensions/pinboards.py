from __future__ import annotations

import asyncio
import sys
import traceback
import typing

import discord
import sqlalchemy
import sqlalchemy.ext.asyncio as async_sqlalchemy
from discord.ext import commands

from src import checks, enums, views
from src.constants import HOME_GUILD_ID
from src.database import tables

if typing.TYPE_CHECKING:
    from src import Bot, Context


# TODO: Lock all commands behind the manage messages permission
class Pinboards(commands.Cog):
    EMOJI_DIGITS = (
        "\N{DIGIT ONE}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}",
        "\N{DIGIT TWO}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}",
        "\N{DIGIT THREE}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}",
        "\N{DIGIT FOUR}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}",
        "\N{DIGIT FIVE}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}",
        "\N{DIGIT SIX}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}",
        "\N{DIGIT SEVEN}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}",
        "\N{DIGIT EIGHT}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}",
        "\N{DIGIT NINE}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}",
    )
    EMOJI_LEFT_ARROW = "\N{LEFTWARDS BLACK ARROW}\N{VARIATION SELECTOR-16}"
    EMOJI_RIGHT_ARROW = "\N{BLACK RIGHTWARDS ARROW}\N{VARIATION SELECTOR-16}"
    EMOJI_CHECKMARK = "\N{WHITE HEAVY CHECK MARK}"
    EMOJI_CROSS = "\N{CROSS MARK}"
    # TODO: Make this configurable just in case Discord decideds to change it
    MAXIMUM_PINNED_MESSAGES_LIMIT = 50

    def __init__(self, bot: "Bot"):
        self.bot = bot

    async def _request_confirmation(self, *, channel: discord.TextChannel, embed: discord.Embed):
        response = await channel.send(embed=embed)

        await response.add_reaction(self.EMOJI_CHECKMARK)
        await response.add_reaction(self.EMOJI_CROSS)

        def can_confirm(reaction: discord.Reaction, user: discord.User | discord.Member):
            if isinstance(user, discord.User):
                print("Ignoring confirmation check as user is not of type discord.Member...")

                return False

            permissions = channel.permissions_for(user)

            return reaction.emoji in [self.EMOJI_CHECKMARK, self.EMOJI_CROSS] and permissions.manage_messages

        try:
            reaction, _user = await self.bot.wait_for("reaction_add", check=can_confirm, timeout=60)
        except asyncio.CancelledError:
            return False

        if reaction.emoji == self.EMOJI_CROSS:
            await response.delete()

            return False

        await response.clear_reactions()

        return True

    def _create_pinboard_channel_paginator(self, channels: list[discord.TextChannel]):
        TOTAL_CHOICES = 9
        # Might need to expose private attributes like the current page
        paginator = commands.Paginator(prefix="", suffix="")

        for index, channel in enumerate(channels):
            index = index % TOTAL_CHOICES
            emoji = self.EMOJI_DIGITS[index]

            try:
                paginator.add_line(f"{emoji}) {channel.mention} (`{channel.id}`)")
            except RuntimeError:
                paginator.close_page()
            else:
                if index == TOTAL_CHOICES - 1:
                    paginator.close_page()

        return paginator.pages

    # TODO: Convert to view
    async def _prompt_pin_migration_channel(
        self,
        *,
        channel: discord.TextChannel,
        pages: list[str],
        pinboard_channels: list[discord.TextChannel],
        author: discord.Member | None = None,
    ):
        TOTAL_PAGES = len(pages)
        current_page_number = 0
        previous_page_number = 0
        current_page = pages[current_page_number]
        embed = discord.Embed(title="Select a \N{PUSHPIN}pinboard to migrate to", description=current_page)
        response = await channel.send(embed=embed)
        selected: discord.TextChannel | None = None

        await response.add_reaction(self.EMOJI_LEFT_ARROW)

        # FIXME: There has to be a better way
        for index in range(current_page.find("\n") + 1):
            emoji = self.EMOJI_DIGITS[index]

            await response.add_reaction(emoji)

        await response.add_reaction(self.EMOJI_RIGHT_ARROW)

        while not selected:
            if current_page_number != previous_page_number:
                embed.description = pages[current_page_number]
                previous_page_number = current_page_number

                await response.edit(embed=embed)

            reaction, user = await self.bot.wait_for(
                "reaction_add",
                check=lambda reaction, user: (
                    (
                        reaction.emoji in [self.EMOJI_LEFT_ARROW, self.EMOJI_RIGHT_ARROW]
                        or reaction.emoji in self.EMOJI_DIGITS
                    )
                    and (user == author)
                    if author
                    else True
                ),
                timeout=60,
            )

            # sourcery skip: simplify-numeric-comparison
            if reaction.emoji == self.EMOJI_LEFT_ARROW and (_can_navigate := current_page_number - 1 >= 0):
                current_page_number -= 1

                await response.remove_reaction(reaction.emoji, user)
            elif reaction.emoji == self.EMOJI_RIGHT_ARROW and (_can_navigate := current_page_number + 1 <= TOTAL_PAGES - 1):
                current_page_number += 1

                await response.remove_reaction(reaction.emoji, user)
            elif reaction.emoji in self.EMOJI_DIGITS:
                index = self.EMOJI_DIGITS.index(reaction.emoji) + current_page_number * 7
                selected = pinboard_channels[index]

                await response.clear_reactions()

        return selected

    # TODO: Refactor to retrieve and cache the number of pinned messages in all
    # linked channels when the bot starts up, with a way to temporarily store
    # increments/decrements of newly un/pinned messages within a linked channel

    # You may need to use Redis for a more persistent cache
    async def _maybe_process_automated_migration(self, *, channel: discord.TextChannel):
        pinned_messages = await channel.pins()

        if len(pinned_messages) != self.MAXIMUM_PINNED_MESSAGES_LIMIT:
            return

        mode = await self.bot.database.get_automatic_migration_mode()

        if mode is enums.AutomaticMigrationMode.MANUAL:
            return

        if mode is enums.AutomaticMigrationMode.CONFIRMATION:
            embed = discord.Embed(
                title="You have reached the maximum number of pinned messages for this channel",
                description="Would you like to migrate these messages to a pinboard?",
            )
            confirmed = await self._request_confirmation(channel=channel, embed=embed)

            if not confirmed:
                return

        pinboard_channel_ids = await self.bot.database.get_pinboard_channel_ids(linked_channel_id=channel.id)
        pinboard_channels = [typing.cast(discord.TextChannel, self.bot.get_channel(id_)) for id_ in pinboard_channel_ids]
        pages = self._create_pinboard_channel_paginator(pinboard_channels)

        await self._prompt_pin_migration_channel(channel=channel, pages=pages, pinboard_channels=pinboard_channels)

    # FIXME: Track older messages using raw event listener
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        # TODO: Use built-in logging instead
        if getattr(before.guild, "id", -1) != HOME_GUILD_ID:
            print("Ignoring message edit in non-home guild...")

            return

        if not isinstance(before.channel, discord.TextChannel):
            print("Ignoring message edit in non-text channel...")

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

        # TODO: Check permissions for the channel to avoid raising an error
        try:
            await before.unpin()
        except discord.Forbidden:
            print("Ignoring unpinning message due to lack of permissions...")

            # TODO: Test this
            await self._maybe_process_automated_migration(channel=before.channel)

    @checks.depends_on("database")
    @commands.group()
    async def pinboards(self, context: Context):
        """
        Display all registered pinboards in the server
        """
        if context.invoked_subcommand:
            return

        view = views.Delete(author=context.author)
        generated_descriptions = ""

        # TODO: Replace with session manager tied to bot which does this for you
        # internally by default
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

    @checks.depends_on("database")
    @commands.command()
    async def migrate(self, context: "Context"):
        """
        Migrates all pinned messages in the current channel to a selected pinboard
        """
        pinboard_channel_ids = await self.bot.database.get_pinboard_channel_ids(linked_channel_id=context.channel.id)
        pinboard_channels = [typing.cast(discord.TextChannel, self.bot.get_channel(id_)) for id_ in pinboard_channel_ids]
        selected_channel: discord.TextChannel | None = None

        # There's no point prompting for selection when there is only one
        # pinboard, might as well automatically select it for the user and skip
        # the unnecessary prompting
        if len(pinboard_channels) == 1:
            selected_channel = pinboard_channels[0]
        else:
            pages = self._create_pinboard_channel_paginator(pinboard_channels)
            selected_channel = await self._prompt_pin_migration_channel(
                author=context.author,
                channel=typing.cast(discord.TextChannel, context.channel),
                pages=pages,
                pinboard_channels=pinboard_channels,
            )

        pinned_messages = await selected_channel.pins()

        for message in reversed(pinned_messages):
            await selected_channel.send(message.content)
            await message.unpin()


async def setup(bot: Bot):
    await bot.add_cog(Pinboards(bot))
