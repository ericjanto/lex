"""
Const
=====
Constants collection place
"""


from dataclasses import dataclass

from ._dbtypes import UposTag
from ._utils import relativy_path


@dataclass
class Const:
    API_DEV_URL = "http://127.0.0.1:8000"

    PATH_BASE_VOCAB = relativy_path(
        "assets/reference-vocabulary/vocabulary.base.txt"
    )

    PATH_IRRELEVANT_VOCAB = relativy_path(
        "assets/reference-vocabulary/vocabulary.irrelevant.txt"
    )

    CONTEXT_LINE_NUM = 5

    UPOS_RELEVANT = [
        UposTag.NOUN.value,
        UposTag.VERB.value,
        UposTag.ADJ.value,
        UposTag.ADV.value,
    ]
