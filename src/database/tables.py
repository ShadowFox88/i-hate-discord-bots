import tortoise
from tortoise import fields

from src import enums

__all__ = (
    "Pinboard",
    "LinkedChannel",
    "GlobalConfiguration",
    "Message",
    "DataProtectedUser",
    "ALL",
)
__models__ = (
    "Pinboard",
    "LinkedChannel",
    "GlobalConfiguration",
    "Message",
    "DataProtectedUser",
)


class Pinboard(tortoise.Model):
    id = fields.IntField(pk=True)
    channel_id = fields.BigIntField(unique=True)


class LinkedChannel(tortoise.Model):
    id = fields.IntField(pk=True)
    channel_id = fields.BigIntField()
    pinboard_channel_id = fields.BigIntField()


class GlobalConfiguration(tortoise.Model):
    automatic_migration_mode = fields.IntEnumField(
        enums.AutomaticMigrationMode, default=enums.AutomaticMigrationMode.CONFIRMATION
    )


class Message(tortoise.Model):
    id = fields.IntField(pk=True, unique=True)
    author_id = fields.IntField()
    channel_id = fields.BigIntField()
    created_at = fields.DatetimeField()
    content = fields.CharField(2000)
    pinned = fields.BooleanField()


class DataProtectedUser(tortoise.Model):
    id = fields.IntField(pk=True, unique=True)


ALL = (Pinboard, LinkedChannel, GlobalConfiguration, Message, DataProtectedUser)
