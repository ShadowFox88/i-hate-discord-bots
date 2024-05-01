from discord.ext import commands

__all__ = ("BaseError", "CheckError", "UnavailableFeature", "DatabaseError", "CannotConnect")


class BaseError(Exception):
    def __init__(self, message: str = ""):
        super().__init__(message)

        self.message = message


class CheckError(BaseError, commands.CommandError):
    pass


class UnavailableFeature(CheckError):
    pass


class DatabaseError(BaseError):
    pass


class CannotConnect(DatabaseError):
    pass
