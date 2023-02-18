def map_iso_lang_to_punkt(iso_lang: str) -> str:
    """
    Maps a ISO 639-1 language code (e.g. en) to
    the language specifer used by the PunktSentenceTokenizer.

    This can be verified in \\nltk_data\\tokenizers\\punkt.
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
            Check \\nltk_data\\tokenizers\\punkt.
            """
        )
