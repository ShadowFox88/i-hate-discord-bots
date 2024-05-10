import enum

__all__ = ("AutomaticMigrationMode",)


class AutomaticMigrationMode(enum.IntEnum):
    AUTOMATED = 1
    CONFIRMATION = 2
    MANUAL = 3
