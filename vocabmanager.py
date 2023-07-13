"""
Vocabulary Manager
==================
Collection of functionality to modify the vocabulary.
"""

from api import ApiEnvironment, ApiRequestor
from const import Const
from textparser import TextParser


class VocabManager:
    """ """

    def __init__(self, api_env: ApiEnvironment) -> None:
        """ """
        self.api = ApiRequestor(api_env)

    def transfer_lemma_to_irrelevant_vocab(self, lemma: str) -> bool:
        lemma_id = self.api.get_lemma_id(lemma)
        if result := self.api.delete_lemma(lemma_id):
            irrelevant_vocab = TextParser._load_vocab(
                Const.PATH_IRRELEVANT_VOCAB
            )
            if lemma not in irrelevant_vocab:
                with open(Const.PATH_IRRELEVANT_VOCAB, "a") as f:
                    f.write(f"{lemma}\n")
        return result
