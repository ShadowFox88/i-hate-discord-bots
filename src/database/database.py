import typing

import discord
import tortoise

from src import CONFIGURATION, flags
from src.errors import CannotConnect

from . import pinboards, tables  # pyright: ignore[reportUnusedImport]

__all__ = (
    "initialise",
    "get_configuration",
    "set_configuration_settings",
    "message_exists_with_id",
    "is_users_data_protected",
    "store_message",
    "get_message",
    "delete_message",
    "prune",
    "close",
)


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


async def get_configuration():
    return await tables.GlobalConfiguration.get()


async def set_configuration_settings(**properties: typing.Any):
    configuration = await get_configuration()

    await configuration.select_for_update().update(**properties)


async def message_exists_with_id(id_: int):
    return await tables.Message.exists(id=id_)


async def is_users_data_protected(*, user_id: int):
    return await tables.DataProtectedUser.exists(id=user_id)


async def store_message(message: discord.Message):
    await tables.Message.create(
        id=message.id,
        author_id=message.author.id,
        channel_id=message.channel.id,
        created_at=message.created_at,
        content=message.content,
        pinned=False,
    )


async def get_message(id_: int):
    return await tables.Message.get(id=id_)


async def delete_message(id_: int):
    message = await tables.Message.get(id=id_)

    await message.delete()


async def prune():
    for table in tables.ALL:
        await table.all().delete()


async def close():
    await tortoise.Tortoise.close_connections()
