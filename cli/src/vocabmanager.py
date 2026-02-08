"""
Vocabulary Manager
==================
Collection of functionality to show and modify the vocabulary.
"""

from datetime import datetime

from .anki import AnkiConnectClient
from .apirequestor import ApiRequestor
from .const import Const
from .dbtypes import LemmaId, StatusVal
from .textparser import TextParser


class VocabManager:
    """ """

    def __init__(self) -> None:
        """ """
        self.api = ApiRequestor()
        self.anki = AnkiConnectClient()

    def transfer_lemma_to_irrelevant_vocab(self, lemma: str) -> bool:
        lemma_id = self.api.get_lemma_id(lemma)
        if result := self.api.delete_lemmata({lemma_id}):
            irrelevant_vocab = TextParser._load_vocab(
                Const.PATH_IRRELEVANT_VOCAB
            )
            if lemma not in irrelevant_vocab:
                with open(Const.PATH_IRRELEVANT_VOCAB, "a") as f, open(
                    Const.PATH_METADATA_DELETION, "a"
                ) as fmeta:
                    f.write(f"{lemma}\n")
                    dt = datetime.now()
                    dt_str = dt.strftime("%Y-%m-%dT%H:%M:%S")
                    fmeta.write(f"{lemma},{dt_str}\n")
        return result

    def transfer_lemmata_to_irrelevant_vocab(
        self, lemma_ids: set[LemmaId]
    ) -> bool:
        irrelevant_vocab = TextParser._load_vocab(Const.PATH_IRRELEVANT_VOCAB)
        with open(Const.PATH_IRRELEVANT_VOCAB, "a") as f, open(
            Const.PATH_METADATA_DELETION, "a"
        ) as fmeta:
            for lid in lemma_ids:
                if (
                    lemma := self.api.get_lemma_name(lid)
                ) and lemma not in irrelevant_vocab:
                    f.write(f"{lemma}\n")
                    dt = datetime.now()
                    dt_str = dt.strftime("%Y-%m-%dT%H:%M:%S")
                    fmeta.write(f"{lemma},{dt_str}\n")
        return self.api.delete_lemmata(lemma_ids)

    def print_staged_lemma_rows(
        self, page: int = 1, page_size: int | None = None
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
        success = self.api.update_multiple_status({lemma_id}, pushed_status_id)
        if success:
            with open(Const.PATH_METADATA_PUSH, "a") as f:
                dt = datetime.now()
                dt_str = dt.strftime("%Y-%m-%dT%H:%M:%S")
                f.write(f"{lemma_id},{dt_str}\n")
        return success

    def push_lemmata(self, lemma_ids: set[LemmaId]):
        pushed_status_id = self.api.post_status(StatusVal.PUSHED)
        success = self.api.update_multiple_status(lemma_ids, pushed_status_id)
        if success:
            with open(Const.PATH_METADATA_PUSH, "a") as f:
                dt = datetime.now()
                dt_str = dt.strftime("%Y-%m-%dT%H:%M:%S")
                for lid in lemma_ids:
                    f.write(f"{lid},{dt_str}\n")
        return success

    def add_to_anki(self, lemma: str) -> bool:
        """
        Adds a lemma and its first context sentence to Anki.
        """
        lemma_id = self.api.get_lemma_id(lemma)
        if lemma_id == -1:
            print(f"Lemma '{lemma}' not found in database.")
            return False

        contexts = self.api.get_lemma_contexts(lemma_id, page=1, page_size=1)
        context_text = (
            contexts[0].context_value if contexts else "No context found."
        )

        result = self.anki.add_note(lemma, context_text)
        if "error" in result and result["error"]:
            print(f"Anki Error: {result['error']}")
            return False

        print(f"Successfully added '{lemma}' to Anki.")
        return True

    def add_lemmata_to_anki(self, lemma_ids: set[LemmaId]) -> bool:
        """
        Adds multiple lemmata to Anki.
        """
        success = True
        for lid in lemma_ids:
            lemma = self.api.get_lemma_name(lid)
            if lemma:
                if not self.add_to_anki(lemma):
                    success = False
        return success
