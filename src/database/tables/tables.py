from __future__ import annotations

import socket
import typing

import sqlalchemy

from src import errors

if typing.TYPE_CHECKING:
    from src import Database

__all__ = (
    "METADATA",
    "PINBOARDS",
    "LINKED_CHANNEL_IDS",
    "maybe_create",
)
METADATA = sqlalchemy.MetaData()
# TODO: Add support for guilds
PINBOARDS = sqlalchemy.Table(
    "pinboards",
    METADATA,
    sqlalchemy.Column("id", sqlalchemy.Integer(), primary_key=True),
    sqlalchemy.Column("channel_id", sqlalchemy.BigInteger(), nullable=False, unique=True),
)
LINKED_CHANNEL_IDS = sqlalchemy.Table(
    "linked_channel_ids",
    METADATA,
    sqlalchemy.Column("id", sqlalchemy.Integer(), primary_key=True),
    sqlalchemy.Column("channel_id", sqlalchemy.BigInteger(), nullable=False),
    sqlalchemy.Column("pinboard_channel_id", sqlalchemy.BigInteger(), nullable=False),
)


async def maybe_create(database: "Database"):
    try:
        async with database.driver.begin() as connection:
            await connection.run_sync(METADATA.create_all)
    # This error is raised when the database is not running and a connection is
    # being established regardless, leading to an attempt at connecting to
    # nothing (lol)
    except socket.gaierror:
        raise errors.CannotConnect from None
    except Exception as error:
        raise errors.CannotConnect from error


async def drop_all(database: "Database"):
    async with database.driver.begin() as connection:
        await connection.run_sync(METADATA.drop_all)
