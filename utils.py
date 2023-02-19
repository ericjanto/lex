def iso_639_1_to_full(iso_lang: str) -> str:
    """
    Maps a ISO 639-1 language code (e.g. en) to
    a full language specifer (as used by the
    PunktSentenceTokenizer).
    """
    map = {
        "cz": "czech",
        "da": "danish",
        "nl": "dutch",
        "en": "english",
        "et": "estonian",
        "fi": "finnish",
        "fr": "french",
        "de": "german",
        "el": "greek",
        "it": "italian",
        "ml": "malayalam",
        "no": "norwegian",
        "pl": "polish",
        "pt": "portuguese",
        "ru": "russian",
        "sl": "slovene",
        "es": "spanish",
        "sv": "swedish",
        "tr": "turkish",
    }

    iso_lang = iso_lang.lower()
    if iso_lang in map:
        return map[iso_lang]
    else:
        raise LookupError(
            f"""
            No corresponding language found for {iso_lang}.
            """
        )

def iso_639_1_to_639_2(iso_lang: str) -> str:
    """
    Maps a ISO 639-1 language code (e.g. en) to
    a ISO 639-2 language code.
    """
    map = {
        "cz": "ces",
        "da": "dan",
        "nl": "dum",
        "en": "eng",
        "et": "est",
        "fi": "fin",
        "fr": "fra",
        "de": "deu",
        "el": "grc",
        "it": "ita",
        "ml": "mal",
        "no": "nor",
        "pl": "pol",
        "pt": "por",
        "ru": "rus",
        "sl": "slv",
        "es": "spa",
        "sv": "swe",
        "tr": "tur",
    }

    iso_lang = iso_lang.lower()
    if iso_lang in map:
        return map[iso_lang]
    else:
        raise LookupError(
            f"""
            No corresponding language found for {iso_lang}.
            """
        )
