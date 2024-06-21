import asyncio
import contextlib

import discord

from src import CONFIGURATION, Bot, database, flags, logs
from src.errors import DatabaseError


async def initialise_database():
    try:
        await database.initialise()
    except DatabaseError as error:
        logs.error(error, message="Failed to initialise database")
        flags.set("NO_DATABASE")


async def main():
    bot = Bot()

    discord.utils.setup_logging()

    try:
        await initialise_database()

        with contextlib.suppress(asyncio.CancelledError, KeyboardInterrupt):
            await bot.start(CONFIGURATION.TOKEN)
    except Exception as error:
        logs.error(error)
    finally:
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
