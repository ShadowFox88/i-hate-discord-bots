import typing

import discord

__all__ = (
    "Feature",
    "PinSupportedChannel",
)
type Feature = typing.Literal["database"]
type PinSupportedChannel = discord.TextChannel | discord.Thread
