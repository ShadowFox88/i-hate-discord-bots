from discord.ext import commands

from src import Context, features, flags
from src.errors import UnavailableFeature
from src.typings import Feature


def depends_on(*features_: Feature):
    async def predicate(_: Context):
        if (database := features.get("database")) in features_ and flags.is_set("NO_DATABASE"):
            raise UnavailableFeature(database)

        return (_CAN_RUN := True)

    return commands.check(predicate)
