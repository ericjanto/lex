"""
Const
=====
Constants collection place
"""

from dataclasses import dataclass
from pathlib import Path

from dbtypes import UposTag


@dataclass
class Const:
    API_DEV_URL = "http://127.0.0.1:8000"

    PATH_BASE_VOCAB = Path("assets/reference-vocabulary/vocabulary.base.txt")
    PATH_IRRELEVANT_VOCAB = Path(
        "assets/reference-vocabulary/vocabulary.irrelevant.txt"
    )

    CONTEXT_LINE_NUM = 5

    UPOS_RELEVANT = [
        UposTag.NOUN.value,
        UposTag.VERB.value,
        UposTag.ADJ.value,
        UposTag.ADV.value,
    ]
