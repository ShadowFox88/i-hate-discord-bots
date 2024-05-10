import asyncio
import contextlib
import sys
import traceback

from src import CONFIGURATION, Bot, database, flags
from src.errors import DatabaseError


async def initialise_database():
    try:
        await database.initialise()
    except DatabaseError as error:
        # TODO: Create custom logger with fancy terminal colours
        error_stack = traceback.format_exception(type(error), error, error.__traceback__)

        print("An error occurred when initialising database:\n\n", *error_stack, file=sys.stderr, sep="")
        flags.set("NO_DATABASE")


async def main():
    bot = Bot()

    try:
        await initialise_database()

        with contextlib.suppress(asyncio.CancelledError, KeyboardInterrupt):
            await bot.start(CONFIGURATION.TOKEN)
    except Exception as error:
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
    finally:
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
