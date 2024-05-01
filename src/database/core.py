import asyncio
import sys

import sqlalchemy.ext.asyncio as async_sqlalchemy

from src import CONFIGURATION
from src.typings import Driver, SessionManager

__all__ = ("Database",)


# TODO: Either this needs to be a module or the design needs to be re-thought
class Database:
    async def _connect_to_driver(self) -> Driver | None:
        for retry_count in range(1, 6):
            try:
                return async_sqlalchemy.create_async_engine(
                    CONFIGURATION.POSTGRES_DSN
                    or f"postgresql+asyncpg://{CONFIGURATION.POSTGRES_USER}:{CONFIGURATION.POSTGRES_PASSWORD}@"
                    f"{CONFIGURATION.POSTGRES_HOST}/{CONFIGURATION.POSTGRES_DATABASE}"
                )
            except Exception as error:
                if retry_count < 5:
                    await asyncio.sleep(10)

                    continue

                raise error

    def __init__(self):
        self.driver: Driver
        self.session_manager: SessionManager

        self._driver_connected = asyncio.Event()

        asyncio.create_task(self.__ainit__())

    async def __ainit__(self):
        if driver_connected := await self._connect_to_driver():
            self.driver = driver_connected
            self.session_manager = async_sqlalchemy.async_sessionmaker(driver_connected)
        else:
            print("Failed to initialise database", file=sys.stderr)

        self._driver_connected.set()

    async def wait_until_ready(self):
        await self._driver_connected.wait()
