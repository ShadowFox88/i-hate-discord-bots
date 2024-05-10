import tortoise
from tortoise import fields

from src import enums

__all__ = ("Pinboards", "LinkedChannelIDs", "GlobalConfiguration", "ALL")
__models__ = ("Pinboards", "LinkedChannelIDs", "GlobalConfiguration")


class Pinboards(tortoise.Model):
    id = fields.IntField(pk=True)
    channel_id = fields.BigIntField(unique=True)


class LinkedChannelIDs(tortoise.Model):
    id = fields.IntField(pk=True)
    channel_id = fields.BigIntField()
    pinboard_channel_id = fields.BigIntField()


class GlobalConfiguration(tortoise.Model):
    automatic_migration_mode = fields.IntEnumField(
        enums.AutomaticMigrationMode, default=enums.AutomaticMigrationMode.CONFIRMATION
    )


ALL = (Pinboards, LinkedChannelIDs, GlobalConfiguration)
