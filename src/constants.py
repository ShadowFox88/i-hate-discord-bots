__all__ = ("HOME_GUILD_ID", "PREFIXES")

HOME_GUILD_ID = 774561547930304536
IMAGINARY_BALLS_SYNONYMS = ["rolleo"]
BALLS_SYNONYMS = [
    "ball",
    "testicle",
    "nut",
    "family jewel",
    "ballock",
    "gonad",
    "male genital",
    "rock",
    "stone",
    "teste",
    "genital",
    *IMAGINARY_BALLS_SYNONYMS,
]
I18N_BALLS_SYNONYMS = ["testicolo", "testicoli"]


def pluralise(text: str):
    case_agnostic = text.lower()

    return text if case_agnostic.endswith("s") else f"{text}s"


PREFIXES = tuple(f"{prefix} " for prefix in [*BALLS_SYNONYMS, *I18N_BALLS_SYNONYMS, *map(pluralise, BALLS_SYNONYMS)])
