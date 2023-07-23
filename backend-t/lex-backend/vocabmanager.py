"""
Vocabulary Manager
==================
Collection of functionality to show and modify the vocabulary.
"""

from typing import Union

from backend.api import ApiEnvironment, ApiRequestor
from backend.const import Const
from backend.dbtypes import LemmaId, StatusVal
from backend.textparser import TextParser


class VocabManager:
    """ """

    def __init__(self, api_env: ApiEnvironment) -> None:
        """ """
        self.api = ApiRequestor(api_env)

    def transfer_lemma_to_irrelevant_vocab(self, lemma: str) -> bool:
        lemma_id = self.api.get_lemma_id(lemma)
        if result := self.api.delete_lemmata({lemma_id}):
            irrelevant_vocab = TextParser._load_vocab(
                Const.PATH_IRRELEVANT_VOCAB
            )
            if lemma not in irrelevant_vocab:
                with open(Const.PATH_IRRELEVANT_VOCAB, "a") as f:
                    f.write(f"{lemma}\n")
        return result

    def transfer_lemmata_to_irrelevant_vocab(
        self, lemma_ids: set[LemmaId]
    ) -> bool:
        irrelevant_vocab = TextParser._load_vocab(Const.PATH_IRRELEVANT_VOCAB)
        with open(Const.PATH_IRRELEVANT_VOCAB, "a") as f:
            for lid in lemma_ids:
                if (
                    lemma := self.api.get_lemma_name(lid)
                ) and lemma not in irrelevant_vocab:
                    f.write(f"{lemma}\n")
        return self.api.delete_lemmata(lemma_ids)

    def print_staged_lemma_rows(
        self, page: int = 1, page_size: Union[int, None] = None
    ) -> None:
        print(
            self.api.get_status_lemmata(
                status_val=StatusVal.STAGED,
                page=page,
                page_size=page_size,
                table=True,
            )
        )

    def commit_lemma(self, lemma: str):
        committed_status_id = self.api.post_status(StatusVal.COMMITTED)
        lemma_id = self.api.get_lemma_id(lemma)
        return self.api.update_multiple_status({lemma_id}, committed_status_id)

    def commit_lemmata(self, lemma_ids: set[LemmaId]):
        committed_status_id = self.api.post_status(StatusVal.COMMITTED)
        return self.api.update_multiple_status(lemma_ids, committed_status_id)

    def push_lemma(self, lemma: str):
        pushed_status_id = self.api.post_status(StatusVal.PUSHED)
        lemma_id = self.api.get_lemma_id(lemma)
        return self.api.update_multiple_status({lemma_id}, pushed_status_id)

    def push_lemmata(self, lemma_ids: set[LemmaId]):
        pushed_status_id = self.api.post_status(StatusVal.PUSHED)
        return self.api.update_multiple_status(lemma_ids, pushed_status_id)
