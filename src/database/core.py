import asyncio

import sqlalchemy.ext.asyncio as async_sqlalchemy

from src import CONFIGURATION
from src.typings import Driver, SessionManager

__all__ = ("Database",)


# TODO: Either this needs to be a module or the design needs to be re-thought
class Database:
    async def _retrieve_driver(self) -> Driver | None:
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

        self._driver_retrieved = asyncio.Event()

        asyncio.create_task(self.__ainit__())

    async def __ainit__(self):
        driver_retrieved = await self._retrieve_driver()

        if driver_retrieved:
            self.driver = driver_retrieved
            self.session_manager = async_sqlalchemy.async_sessionmaker(bind=self.driver)

        self._driver_retrieved.set()

    async def wait_until_ready(self):
        await self._driver_retrieved.wait()
