import dataclasses
import inspect
import typing

import dotenv

__all__ = ("CONFIGURATION",)


# TODO: Make mandatory
@dataclasses.dataclass
class Configuration:
    POSTGRES_DATABASE: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    TOKEN: str

    POSTGRES_DSN: str = ""
    POSTGRES_HOST: str = "localhost:5432"

    @classmethod
    def from_dict(cls, raw_environment: dict[str, typing.Any]):
        return cls(**{key: value for key, value in raw_environment.items() if key in inspect.signature(cls).parameters})


raw_configuration = dotenv.dotenv_values()
CONFIGURATION = Configuration.from_dict(raw_configuration)
