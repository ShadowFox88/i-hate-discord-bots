import typing

import sqlalchemy.ext.asyncio as async_sqlalchemy

__all__ = (
    "Driver",
    "SessionManager",
    "Feature",
)
type Driver = async_sqlalchemy.AsyncEngine
type SessionManager = async_sqlalchemy.async_sessionmaker[async_sqlalchemy.AsyncSession]
type Feature = typing.Literal["database"]
