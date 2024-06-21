import logging
import traceback

__all__ = (
    "info",
    "error",
    "format_exception",
)


def info(message: str):
    logging.info(message)


def error(error: BaseException, *, message: str = ""):
    stack = "".join(traceback.format_exception(type(error), error, error.__traceback__))

    if message:
        logging.error(f"{message}:\n\n{stack}")
    else:
        logging.error(stack)


def format_exception(error: BaseException) -> str:
    return "".join(traceback.format_exception(type(error), error, error.__traceback__))
