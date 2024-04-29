import asyncio
import contextlib
import traceback

from src import CONFIGURATION, Bot, Database
from src.database import tables


async def main():
    database = Database()

    await database.wait_until_ready()
    await tables.maybe_create(database)

    bot = Bot(database=database)

    try:
        with contextlib.suppress(asyncio.CancelledError, KeyboardInterrupt):
            await bot.start(CONFIGURATION.TOKEN)
    except Exception as error:
        traceback.print_exception(type(error), error, error.__traceback__)
    finally:
        await bot.close()
        await database.driver.dispose()


if __name__ == "__main__":
    asyncio.run(main())
