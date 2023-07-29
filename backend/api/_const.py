"""
Const
=====
Constants collection place
"""


from dataclasses import dataclass

from ._dbtypes import UposTag
from ._utils import absolutify_path_from_root


@dataclass
class Const:
    API_LOCAL_URL = "http://127.0.0.1:8000"

    PATH_BASE_VOCAB = absolutify_path_from_root(
        "/backend/assets/reference-vocabulary/vocabulary.base.txt"
    )

    PATH_IRRELEVANT_VOCAB = absolutify_path_from_root(
        "/backend/assets/reference-vocabulary/vocabulary.irrelevant.txt"
    )

    SPILL_LINE_NUM = 3
    CONTEXT_LINE_NUM = 10

    UPOS_RELEVANT = [
        UposTag.NOUN.value,
        UposTag.VERB.value,
        UposTag.ADJ.value,
        UposTag.ADV.value,
    ]
