from __future__ import annotations

import asyncio
import typing

import discord
from discord.ext import commands

from src import checks, database, enums, logs, views
from src.constants import HOME_GUILD_ID
from src.database import tables
from src.typings import PinSupportedChannel

if typing.TYPE_CHECKING:
    from src import Bot, Context


# TODO: Rethink design with a clear mind
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
    PIN_SUPPORTED_CHANNEL_TYPES = (
        discord.TextChannel,
        discord.Thread,
    )

    def __init__(self, bot: "Bot"):
        self.bot = bot

    async def _request_confirmation(self, *, channel: PinSupportedChannel, embed: discord.Embed):
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

    def _create_pinboard_channel_paginator(self, channels: list[PinSupportedChannel]):
        TOTAL_CHOICES = 9
        # Might need to expose private attributes like the current page
        paginator = commands.Paginator(prefix="", suffix="")

        for index, channel in enumerate(channels):
            index = index % TOTAL_CHOICES
            emoji = self.EMOJI_DIGITS[index]

            try:
                paginator.add_line(
                    f"{emoji}) {
                        channel.mention} (`{channel.id}`)"
                )
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
        channel: PinSupportedChannel,
        pages: list[str],
        pinboard_channels: list[PinSupportedChannel],
        author: discord.Member | None = None,
    ):
        TOTAL_PAGES = len(pages)
        current_page_number = 0
        previous_page_number = 0
        current_page = pages[current_page_number]
        embed = discord.Embed(title="Select a \N{PUSHPIN}pinboard to migrate to", description=current_page)
        response = await channel.send(embed=embed)
        selected: PinSupportedChannel | None = None

        await response.add_reaction(self.EMOJI_LEFT_ARROW)

        for index in range(current_page.count("\n")):
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
    async def _maybe_process_automated_migration(self, *, channel: PinSupportedChannel):
        pinned_messages = await channel.pins()

        if len(pinned_messages) != self.MAXIMUM_PINNED_MESSAGES_LIMIT:
            return

        configuration = await database.get_configuration()
        mode = configuration.automatic_migration_mode

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

        pinboard_channel_ids = await database.get_pinboard_channel_ids(linked_channel_id=channel.id)
        pinboard_channels = [typing.cast(PinSupportedChannel, self.bot.get_channel(id_)) for id_ in pinboard_channel_ids]
        pages = self._create_pinboard_channel_paginator(pinboard_channels)

        await self._prompt_pin_migration_channel(channel=channel, pages=pages, pinboard_channels=pinboard_channels)

    async def _maybe_fetch_channel(self, id_: int):
        if channel_found := self.bot.get_channel(id_):
            return channel_found

        return await self.bot.fetch_channel(id_)

    async def _maybe_fetch_text_channel(self, id_: int):
        channel = await self._maybe_fetch_channel(id_)

        assert isinstance(channel, self.PIN_SUPPORTED_CHANNEL_TYPES)

        return channel

    def cog_check(self, context: "Context"):
        return context.channel.permissions_for(context.author).manage_messages

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if _users_datas_protected := await database.is_users_data_protected(user_id=message.author.id):
            return

        await database.store_message(message)

    async def _maybe_fetch_message(self, id_: int, *, cached_message: discord.Message | None, channel: PinSupportedChannel):
        try:
            return cached_message or await channel.fetch_message(id_)
        except discord.HTTPException as error:
            logs.error(error, message="An error occurred when fetching message")

            return None

    async def _maybe_fetch_stored_message(
        self, id_: int, *, cached_message: discord.Message | None, channel: PinSupportedChannel
    ):
        if cached_message:
            return cached_message
        elif stored_message_found := await database.get_message(id_):
            return stored_message_found

        return await self._maybe_fetch_message(id_, cached_message=cached_message, channel=channel)

    async def _process_pinned_message(
        self, *, channel: PinSupportedChannel, linked_channel_id: int, previous_message: discord.Message | tables.Message
    ):
        channel_ids_found = await database.get_pinboard_channel_ids(linked_channel_id=linked_channel_id)

        if not channel_ids_found:
            print("Ignoring message edit due to no linked channels...")

            return

        error_raised = False

        for id_ in channel_ids_found:
            pinboard_channel_found = self.bot.get_channel(id_)

            if not (pinboard_channel_found and isinstance(pinboard_channel_found, self.PIN_SUPPORTED_CHANNEL_TYPES)):
                print(f"Ignoring channel with ID {id_}")

                continue

            try:
                await pinboard_channel_found.send(previous_message.content)
            except Exception as error:
                if not error_raised:
                    error_raised = True

                logs.error(error)

        if error_raised:
            return

        if isinstance(previous_message, tables.Message):
            await previous_message.delete()

            previous_message = await channel.fetch_message(previous_message.id)

        # TODO: Check permissions for the channel to avoid raising an error
        try:
            await previous_message.unpin()
        except discord.Forbidden:
            print("Ignoring unpinning message due to lack of permissions...")

            # TODO: Test this
            await self._maybe_process_automated_migration(channel=channel)

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent):
        # TODO: Use built-in logging instead
        if payload.guild_id != HOME_GUILD_ID:
            print("Ignoring message edit in non-home guild...")

            return

        channel = await self._maybe_fetch_channel(payload.channel_id)

        if not isinstance(channel, self.PIN_SUPPORTED_CHANNEL_TYPES):
            print("Ignoring message edit in non-text channel...")

            return

        if not (
            previous_message_found := await self._maybe_fetch_stored_message(
                payload.message_id, cached_message=payload.cached_message, channel=channel
            )
        ):
            print("Ignoring message edit as unable to compare pin status of non-existant, prior message state...")

            return

        new_message = await channel.fetch_message(payload.message_id)

        if _message_was_pinned := not previous_message_found.pinned and new_message.pinned:
            await self._process_pinned_message(
                channel=channel, linked_channel_id=payload.channel_id, previous_message=previous_message_found
            )
        elif _message_wa_edited := previous_message_found.content != new_message.content:
            if isinstance(previous_message_found, tables.Message):
                await previous_message_found.select_for_update().update(content=new_message.content)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        if not await database.message_exists_with_id(payload.message_id):
            return

        if not (message_found := payload.cached_message):
            # Given the context of this event, both the channel and message are
            # guaranteed to exist so the typecast is safe
            channel = await self._maybe_fetch_text_channel(payload.channel_id)
            message_found = typing.cast(
                discord.Message,
                await self._maybe_fetch_message(payload.message_id, cached_message=payload.cached_message, channel=channel),
            )

        try:
            await message_found.delete()
            await database.delete_message(payload.message_id)
        except discord.HTTPException as error:
            logs.error(error, message="An error occurred when invalidating message from database")

    @checks.depends_on("database")
    @commands.group()
    async def pinboards(self, context: Context):
        """
        Display all registered pinboards in the server
        """
        if context.invoked_subcommand:
            return

        view = views.Delete(author=context.author)
        rows = await tables.Pinboard.all().order_by("channel_id").limit(6)
        # sourcery skip: use-or-for-fallback
        description = "\n".join(f"<#{row.channel_id}>" for row in rows)

        if not description:
            # TODO: Create or use a third-party module that allows me to
            # reference these emojis by name and provides auto-complete instead
            # of relying on strings that could potentially be misspelled/misremembered
            description = (
                "\N{CROSS MARK} You do not have any pinboards registered in this server!\n"
                "\n"
                "\N{LEFT SPEECH BUBBLE}\N{VARIATION SELECTOR-16} \N{ROBOT FACE} To create one, use `pinboard add #channel`, where `#channel` is the text channel to transform into a pinboard."
            )

        embed = discord.Embed(title="\N{PUSHPIN} Pinboards", description=description)

        await context.send(embed=embed, view=view)

    @checks.depends_on("database")
    @pinboards.command(name="add")
    async def pinboard_add(self, context: Context, channel: PinSupportedChannel):
        """
        Add a channel to register as a pinboard
        """
        await database.create_pinboard(channel_id=channel.id)
        await context.send(f"Registered {channel.mention} as a pinboard!")

    @checks.depends_on("database")
    @pinboards.command(name="link")
    async def pinboard_link(
        self, context: Context, channel_to_link: PinSupportedChannel, pinboard_channel: PinSupportedChannel
    ):
        """
        Assign a channel to an existing pinboard
        """
        await database.link_channel_to_pinboard(channel_id=channel_to_link.id, pinboard_channel_id=pinboard_channel.id)
        await context.send(f"Successfully linked {channel_to_link.mention} to the \N{PUSHPIN}{pinboard_channel.mention}")

    @checks.depends_on("database")
    @commands.command()
    async def migrate(self, context: "Context"):
        """
        Migrates all pinned messages in the current channel to a selected pinboard
        """
        pinboard_channel_ids = await database.get_pinboard_channel_ids(linked_channel_id=context.channel.id)
        pinboard_channels = [typing.cast(PinSupportedChannel, self.bot.get_channel(id_)) for id_ in pinboard_channel_ids]

        assert isinstance(context.channel, self.PIN_SUPPORTED_CHANNEL_TYPES)

        selected_channel: PinSupportedChannel | None = None

        # There's no point prompting for selection when there is only one
        # pinboard, might as well automatically select it for the user and skip
        # the unnecessary prompting
        if len(pinboard_channels) == 1:
            selected_channel = pinboard_channels[0]
        else:
            pages = self._create_pinboard_channel_paginator(pinboard_channels)
            selected_channel = await self._prompt_pin_migration_channel(
                author=context.author,
                channel=context.channel,
                pages=pages,
                pinboard_channels=pinboard_channels,
            )

        pinned_messages = await selected_channel.pins()

        for message in reversed(pinned_messages):
            await selected_channel.send(message.content)
            await message.unpin()


async def setup(bot: Bot):
    await bot.add_cog(Pinboards(bot))
