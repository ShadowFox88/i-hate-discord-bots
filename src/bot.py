from __future__ import annotations

import pkgutil
import traceback

import discord
from discord.ext import commands

from src.constants import PREFIXES

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

    async def load_extensions(self):
        folder_path = "src/extensions"
        folder_path_as_module = folder_path.replace("/", ".")
        logs: list[str] = []

        await self.load_extension("jishaku")

        for module_info in pkgutil.walk_packages([folder_path], prefix=f"{folder_path_as_module}."):
            module_path = module_info.name

            # TODO: Override this and other related methods to log during operations
            try:
                await self.load_extension(module_path)
            except Exception as error:
                traceback_ = "".join(traceback.format_exception(type(error), error, error.__traceback__))

                logs.append(f"An error occurred when loading {module_path}:\n\n{traceback_}")
            else:
                logs.append(f"Successfully loaded {module_path}")

        print(*logs, sep="\n", end="\n\n")

    async def setup_hook(self):
        await self.load_extensions()

        if self.user:
            print(self.user.name)
