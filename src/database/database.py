import typing

import tortoise

from src import CONFIGURATION, flags
from src.errors import CannotConnect

from . import tables


async def initialise():
    url = CONFIGURATION.POSTGRES_DSN or (
        f"postgres://{CONFIGURATION.POSTGRES_USER}:{CONFIGURATION.POSTGRES_PASSWORD}@"
        f"{CONFIGURATION.POSTGRES_HOST}/{CONFIGURATION.POSTGRES_DATABASE}"
    )

    try:
        # I don't think the unknown types from the configuration are something
        # that an end user is meant to resolve
        await tortoise.Tortoise.init(  # type: ignore
            db_url=url,
            modules={"models": ["src.database"]},
        )
        await tortoise.Tortoise.generate_schemas()
        await tables.GlobalConfiguration.create()
    except Exception as error:
        flags.set("NO_DATABASE")

        raise CannotConnect from error


async def create_pinboard(*, channel_id: int):
    await tables.Pinboards.create(channel_id=channel_id)


async def get_pinboard_channel_ids(*, linked_channel_id: int):
    rows = await tables.LinkedChannelIDs.all().filter(channel_id=linked_channel_id)

    return [row.pinboard_channel_id for row in rows]


async def link_channel_to_pinboard(*, channel_id: int, pinboard_channel_id: int):
    await tables.LinkedChannelIDs.create(channel_id=channel_id, pinboard_channel_id=pinboard_channel_id)


async def get_configuration():
    return await tables.GlobalConfiguration.get()


async def set_configuration_settings(**properties: typing.Any):
    configuration = await get_configuration()

    await configuration.select_for_update().update(**properties)


async def prune():
    for table in tables.ALL:
        await table.all().delete()


async def close():
    await tortoise.Tortoise.close_connections()
