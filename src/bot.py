from __future__ import annotations

import pkgutil

import discord
from discord.ext import commands

from src import logs
from src.constants import HOME_GUILD_ID, PREFIXES

__all__ = ("Bot",)

INTENTS = discord.Intents(
    guild_messages=True, guild_reactions=True, guilds=True, members=True, message_content=True, reactions=True
)


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or(*PREFIXES),
            intents=INTENTS,
        )

        self.home_guild: discord.Guild

    async def load_extension(self, name: str, *, package: str | None = None):
        try:
            await super().load_extension(name, package=package)
        except Exception as error:
            logs.error(error, message=f"An error occurred when loading {name}")
        else:
            logs.info(f"Successfully loaded {name}")

    async def load_extensions(self):
        folder_path = "src/extensions"
        folder_path_as_module = folder_path.replace("/", ".")

        await self.load_extension("jishaku")

        for module_info in pkgutil.walk_packages([folder_path], prefix=f"{folder_path_as_module}."):
            module_path = module_info.name

            await self.load_extension(module_path)

    async def setup_hook(self):
        if not (home_guild_found := self.get_guild(HOME_GUILD_ID)):
            raise ValueError(f"Home guild not found with ID {HOME_GUILD_ID}")

        self.home_guild = home_guild_found

        await self.load_extensions()

        if self.user:
            print(self.user.name)
