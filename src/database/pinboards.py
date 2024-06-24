from . import tables

__all__ = (
    "create",
    "get_all_channel_ids",
    "get_channel_ids_for",
    "link_channel",
)


async def create(*, channel_id: int):
    await tables.Pinboard.create(channel_id=channel_id)


async def get_all_channel_ids():
    return [row.pinboard_channel_id for row in await tables.LinkedChannel.all()]


async def get_channel_ids_for(*, linked_channel_id: int):
    return [row.pinboard_channel_id for row in await tables.LinkedChannel.all().filter(channel_id=linked_channel_id)]


async def link_channel(*, channel_id: int, pinboard_channel_id: int):
    await tables.LinkedChannel.create(channel_id=channel_id, pinboard_channel_id=pinboard_channel_id)
