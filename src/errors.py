from discord.ext import commands

from src.typings import Feature

__all__ = ("BaseError", "CheckError", "UnavailableFeature", "DatabaseError", "CannotConnect", "NoConfigurationFound")


class BaseError(Exception):
    def __init__(self, message: str = ""):
        super().__init__(message)

        self.message = message


class CheckError(BaseError, commands.CommandError):
    pass


class UnavailableFeature(CheckError):
    def __init__(self, name: Feature):
        super().__init__(name)


class DatabaseError(BaseError):
    pass


class CannotConnect(DatabaseError):
    pass


class NoConfigurationFound(DatabaseError):
    pass
