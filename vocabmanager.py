"""
Vocabulary Manager
==================
Collection of functionality to show and modify the vocabulary.
"""

from api import ApiEnvironment, ApiRequestor
from const import Const
from dbtypes import StatusVal
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

    def list_pending_lemma_rows(self, head: int | None = None) -> None:
        print(self.api.get_pending_lemma_rows(head))

    def accept_lemma(self, lemma: str):
        pending_status_id = self.api.get_lemma_status(StatusVal.ACCEPTED)
        lemma_id = self.api.get_lemma_id(lemma)
        return self.api.update_status(lemma_id, pending_status_id)
