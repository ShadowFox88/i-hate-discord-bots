import asyncio
import contextlib
import sys
import traceback

from src import CONFIGURATION, Bot, Database, flags
from src.database import tables
from src.errors import DatabaseError


async def initialise_database():
    database = None

    try:
        database = Database()

        await database.wait_until_ready()
        await tables.maybe_create(database)
    except DatabaseError as error:
        # TODO: Create custom logger with fancy terminal colours
        error_stack = traceback.format_exception(type(error), error, error.__traceback__)

        flags.set("NO_DATABASE")
        print("An error occurred when initialising database:\n\n", *error_stack, file=sys.stderr, sep="")

    return database


async def main():
    database = await initialise_database()
    bot = Bot(database=database)

    try:
        with contextlib.suppress(asyncio.CancelledError, KeyboardInterrupt):
            await bot.start(CONFIGURATION.TOKEN)
    except Exception as error:
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
    finally:
        await bot.close()

        if not database:
            return

        await database.driver.dispose()


if __name__ == "__main__":
    asyncio.run(main())
