import enum

__all__ = ("AutomaticMigrationMode",)


class AutomaticMigrationMode(enum.Enum):
    AUTOMATED = 1
    CONFIRMATION = 2
    MANUAL = 3
