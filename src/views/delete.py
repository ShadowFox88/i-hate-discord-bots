import typing

import discord


class Delete(discord.ui.View):
    def __init__(self, *, author: discord.Member):
        super().__init__()

        self.author = author

    @discord.ui.button(emoji="\N{WASTEBASKET}", style=discord.ButtonStyle.red)
    async def delete(self, interaction: discord.Interaction, _button: discord.ui.Button[typing.Self]):
        if interaction.message:
            await interaction.message.delete()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user == self.author:
            return True
        elif interaction.channel:
            permissions = interaction.channel.permissions_for(self.author)

            return permissions.manage_messages

        # should be impossible to get here but we special case as a precaution
        return False
