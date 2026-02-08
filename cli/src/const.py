"""
Const
=====
Constants collection place
"""


from dataclasses import dataclass

from .dbtypes import UposTag
from .utils import absolutify_path_from_root


@dataclass
class Const:
    API_LOCAL_URL = "http://127.0.0.1:8000"
    API_PROD_URL = "https://lex.ericjanto.com"

    PATH_BASE_VOCAB = absolutify_path_from_root(
        "/assets/reference-vocabulary/vocabulary.base.txt"
    )

    PATH_IRRELEVANT_VOCAB = absolutify_path_from_root(
        "/assets/reference-vocabulary/vocabulary.irrelevant.txt"
    )

    PATH_METADATA_DELETION = absolutify_path_from_root(
        "/assets/metadata/deletion.csv"
    )

    PATH_METADATA_PUSH = absolutify_path_from_root("/assets/metadata/push.csv")

    SPILL_LINE_NUM = 3
    CONTEXT_LINE_NUM = 10

    UPOS_RELEVANT = [
        UposTag.NOUN.value,
        UposTag.VERB.value,
        UposTag.ADJ.value,
        UposTag.ADV.value,
    ]

    import os

    ANKI_URL = os.getenv("ANKI_URL", "http://localhost:8765")
    ANKI_DEFAULT_DECK = os.getenv("ANKI_DECK", "Lex")
    ANKI_DEFAULT_NOTE_TYPE = os.getenv("ANKI_NOTE_TYPE", "Basic")
