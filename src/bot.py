from __future__ import annotations

import pkgutil
import traceback
import typing

import discord
from discord.ext import commands

from src.constants import PREFIXES

if typing.TYPE_CHECKING:
    from src import Database

__all__ = ("Bot",)
IMAGINARY_BALLS_SYNONYMS = ["rolleo"]
BALLS_SYNONYMS = [
    "ball",
    "testicle",
    "nut",
    "family jewel",
    "ballock",
    "gonad",
    "male genital",
    "rock",
    "stone",
    "teste",
    "genital",
    *IMAGINARY_BALLS_SYNONYMS,
]
I18N_BALLS_SYNONYMS = ["testicolo", "testicoli"]
INTENTS = discord.Intents(
    guild_messages=True, guild_reactions=True, guilds=True, members=True, message_content=True, messages=True, reactions=True
)


def pluralise(text: str):
    case_agnostic = text.lower()

    return text if case_agnostic.endswith("s") else f"{text}s"


class Bot(commands.Bot):
    def __init__(self, *, database: Database | None = None):
        super().__init__(
            command_prefix=commands.when_mentioned_or(*PREFIXES),
            intents=INTENTS,
        )

        if database:
            self.database = database
            self.sessions = database.session_manager

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

    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if _message_was_pinned := before.pinned is False and after.pinned is True:
            pass
        else:
            pass
