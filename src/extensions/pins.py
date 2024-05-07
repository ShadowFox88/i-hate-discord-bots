from __future__ import annotations

import typing

import discord
from discord.ext import commands

from src import checks

if typing.TYPE_CHECKING:
    from src import Bot, Context


class Pins(commands.Cog):
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
    LEFT_ARROW_EMOJI = "\N{LEFTWARDS BLACK ARROW}\N{VARIATION SELECTOR-16}"
    RIGHT_ARROW_EMOJI = "\N{BLACK RIGHTWARDS ARROW}\N{VARIATION SELECTOR-16}"

    def __init__(self, bot: "Bot"):
        self.bot = bot

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

    async def _prompt_pin_migration_channel(
        self,
        *,
        author: discord.Member,
        channel: discord.TextChannel,
        pages: list[str],
        pinboard_channels: list[discord.TextChannel],
    ):
        TOTAL_PAGES = len(pages)
        current_page_number = 0
        previous_page_number = 0
        current_page = pages[current_page_number]
        embed = discord.Embed(title="Select a \N{PUSHPIN}pinboard to migrate to", description=current_page)
        response = await channel.send(embed=embed)
        selected: discord.TextChannel | None = None

        await response.add_reaction(self.LEFT_ARROW_EMOJI)

        # FIXME: There has to be a better way
        for index in range(current_page.find("\n") + 1):
            emoji = self.EMOJI_DIGITS[index]

            await response.add_reaction(emoji)

        await response.add_reaction(self.RIGHT_ARROW_EMOJI)

        while not selected:
            if current_page_number != previous_page_number:
                embed.description = pages[current_page_number]
                previous_page_number = current_page_number

                await response.edit(embed=embed)

            reaction, user = await self.bot.wait_for(
                "reaction_add",
                check=lambda reaction, user: (
                    reaction.emoji in [self.LEFT_ARROW_EMOJI, self.RIGHT_ARROW_EMOJI] or reaction.emoji in self.EMOJI_DIGITS
                )
                and user == author,
                timeout=60,
            )

            # sourcery skip: simplify-numeric-comparison
            if reaction.emoji == self.LEFT_ARROW_EMOJI and (_can_navigate := current_page_number - 1 >= 0):
                current_page_number -= 1

                await response.remove_reaction(reaction.emoji, user)
            elif reaction.emoji == self.RIGHT_ARROW_EMOJI and (_can_navigate := current_page_number + 1 <= TOTAL_PAGES - 1):
                current_page_number += 1

                await response.remove_reaction(reaction.emoji, user)
            elif reaction.emoji in self.EMOJI_DIGITS:
                index = self.EMOJI_DIGITS.index(reaction.emoji) + current_page_number * 7
                selected = pinboard_channels[index]

                await response.clear_reactions()

        return selected

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


async def setup(bot: "Bot"):
    await bot.add_cog(Pins(bot))
