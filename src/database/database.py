from __future__ import annotations

import asyncio
import sys
import typing

import sqlalchemy
import sqlalchemy.ext.asyncio as async_sqlalchemy

from src import CONFIGURATION, enums, errors

from . import tables

if typing.TYPE_CHECKING:
    from src.typings import Driver, SessionManager


__all__ = ("Database",)


# TODO: Either this needs to be a module or the design needs to be re-thought
# TODO: Refactor
class Database:
    async def _connect_to_driver(self) -> "Driver | None":
        for retry_count in range(1, 6):
            try:
                # TODO: Refactor
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

    async def create_pinboard(self, channel_id: int):
        await self.wait_until_ready()

        async with self.session_manager.begin() as session:
            await session.execute(tables.PINBOARDS.insert().values(channel_id=channel_id))

    async def prune(self):
        await self.wait_until_ready()

        async with self.driver.begin() as connection:
            await connection.run_sync(tables.METADATA.drop_all)

    async def get_pinboard_channel_ids(self, linked_channel_id: int) -> list[int]:
        await self.wait_until_ready()

        async with self.session_manager.begin() as session:
            result: sqlalchemy.Result[tuple[int]] = await session.execute(
                sqlalchemy.select(tables.LINKED_CHANNEL_IDS.columns.pinboard_channel_id).where(
                    tables.LINKED_CHANNEL_IDS.columns.channel_id == linked_channel_id
                )
            )

            return [row.pinboard_channel_id for row in result.fetchall()]

    async def link_channel_to_pinboard(self, channel_id: int, pinboard_channel_id: int):
        await self.wait_until_ready()

        async with self.session_manager.begin() as session:
            await session.execute(
                tables.LINKED_CHANNEL_IDS.insert().values(channel_id=channel_id, pinboard_channel_id=pinboard_channel_id)
            )

    async def get_automatic_migration_mode(self) -> enums.AutomaticMigrationMode:
        await self.wait_until_ready()

        async with self.session_manager.begin() as session:
            result: sqlalchemy.Result[tuple[enums.AutomaticMigrationMode]] = await session.execute(
                sqlalchemy.select(tables.GLOBAL_CONFIGURATION)
            )

            if row_found := result.fetchone():
                return row_found.automatic_migration_mode

            raise errors.NoConfigurationFound
