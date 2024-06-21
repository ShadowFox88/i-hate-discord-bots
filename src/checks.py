from __future__ import annotations

import typing

from discord.ext import commands

from src import errors, flags

if typing.TYPE_CHECKING:
    from src import Context
    from src.typings import Feature


def depends_on(*features_: "Feature"):
    async def predicate(_: Context):
        if "database" in features_ and flags.is_set("NO_DATABASE"):
            raise errors.UnavailableFeature("database")

        return (_CAN_RUN := True)

    return commands.check(predicate)
