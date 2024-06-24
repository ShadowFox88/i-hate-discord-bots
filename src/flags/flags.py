import typing

from src import logs

type Flag = typing.Literal["NO_DATABASE"]

__all__ = (
    "Flag",
    "all",
    "is_set",
    "set",
    "unset",
)
flags: set[Flag] = set()


def all():
    return flags.copy()


def is_set(name: Flag):
    return name in flags


def set(name: Flag):
    logs.info(f"Set {name}")

    flags.add(name)


def unset(name: Flag):
    logs.info(f"Unset {name}")
    flags.remove(name)
