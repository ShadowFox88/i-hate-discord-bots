from src.typings import Feature

__all__ = ("get",)


# TODO: Look into a better way to do this
# We create a no-op purely for auto-complete
def get(name: Feature):
    return name
