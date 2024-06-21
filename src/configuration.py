import dotenv
from pydantic import BaseModel

__all__ = ("CONFIGURATION",)


class Configuration(BaseModel):
    POSTGRES_DATABASE: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    TOKEN: str

    POSTGRES_DSN: str = ""
    POSTGRES_HOST: str = "localhost:5432"


CONFIGURATION = Configuration.model_validate(dotenv.dotenv_values(), strict=True)
