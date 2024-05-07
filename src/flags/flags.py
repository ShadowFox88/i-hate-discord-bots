# TODO: Add logging to notify when individual flags are manipulated
import typing

type Flag = typing.Literal["NO_DATABASE"]

__all__ = ("Flag", "all", "is_set", "set", "unset")
flags: set[Flag] = set()


def all():
    return flags.copy()


def is_set(name: Flag):
    return name in flags


def set(name: Flag):
    flags.add(name)


def unset(name: Flag):
    flags.remove(name)
