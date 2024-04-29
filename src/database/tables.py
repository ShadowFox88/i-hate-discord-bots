from __future__ import annotations

import typing

import sqlalchemy

if typing.TYPE_CHECKING:
    from .core import Database

__all__ = (
    "METADATA",
    "PINBOARD",
    "LINKED_CHANNEL_IDS",
    "maybe_create",
)
METADATA = sqlalchemy.MetaData()
PINBOARD = sqlalchemy.Table(
    "pinboard",
    METADATA,
    sqlalchemy.Column("id", sqlalchemy.Integer(), primary_key=True),
    sqlalchemy.Column("channel_id", sqlalchemy.BigInteger(), nullable=False),
)
LINKED_CHANNEL_IDS = sqlalchemy.Table(
    "linked_channel_ids",
    METADATA,
    sqlalchemy.Column("id", sqlalchemy.Integer(), primary_key=True),
    sqlalchemy.Column("channel_id", sqlalchemy.BigInteger(), nullable=False),
    sqlalchemy.Column(
        "pinboard_channel_id", sqlalchemy.BigInteger(), sqlalchemy.ForeignKey(PINBOARD.columns.id), nullable=False
    ),
)


async def maybe_create(database: "Database"):
    async with database.driver.begin() as connection:
        await connection.run_sync(METADATA.create_all)
