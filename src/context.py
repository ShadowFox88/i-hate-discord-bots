import functools
import typing

import discord
from discord.ext import commands

if typing.TYPE_CHECKING:
    from src import Bot


__all__ = ("Context",)


class Context(commands.Context["Bot"]):
    @functools.cached_property
    def author(self) -> discord.Member:
        return self.author
