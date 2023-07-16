"""
Text-Parser
===========
Parses text, extracts relevant lemmeta, adds to the vocabulary
via the API.
"""


import json
from itertools import islice
from typing import NamedTuple

import en_core_web_trf
import spacy
from rich.progress import Progress
from spacy.tokens import Doc, Token

from backend.api import ApiEnvironment, ApiRequestor
from backend.const import Const
from backend.dbtypes import LemmaId, SourceMetadata, StatusVal, UposTag
from backend.utils import buf_count_newlines


class IntermediaryDbDatum(NamedTuple):
    lemma: str
    lemma_id: LemmaId
    tag: str
    pos: UposTag


class TextParser:
    """
    Parsing class which extracts vocabulary from text.
    """

    def __init__(self, api_env: ApiEnvironment) -> None:
        """
        TODO

        - passing some shared args to self.parse instead of
          creating class members as nlp load time is long, and
          this allows us to reuse the same instance for parsing of
          multiple documents
        """
        self.api = ApiRequestor(api_env)

        self.nlp = en_core_web_trf.load()
        self._customise_tokenisation()
        self.nlp_parsing_pipes = self.nlp.select_pipes(
            enable=(
                "transformer",
                "tagger",
                "attribute_ruler",
                "lemmatizer",
            )
        )

    def parse_into_base_vocab(self, content_path: str):
        """ """
        existing_base_vocab = self._load_vocab(Const.PATH_BASE_VOCAB)
        existing_irrelevant_vocab = self._load_vocab(
            Const.PATH_IRRELEVANT_VOCAB
        )
        new_base_vocab: set[str] = set()

        content_line_num = buf_count_newlines(content_path)

        with self.nlp_parsing_pipes, open(content_path) as f, Progress() as p:
            task = p.add_task(
                "[yellow]Parsing into base vocabulary", total=content_line_num
            )

            batch = " "
            while batch:
                batch = " ".join(
                    [
                        line.strip()
                        for line in islice(f, Const.CONTEXT_LINE_NUM)
                    ]
                )

                filtered_doc = filter(
                    lambda t: self._is_relevant_token(
                        t, existing_base_vocab, existing_irrelevant_vocab
                    ),
                    self.nlp(batch),
                )

                for t in filtered_doc:
                    new_base_vocab.add(t.lemma_.lower())

                p.advance(task, Const.CONTEXT_LINE_NUM)

        with open(Const.PATH_BASE_VOCAB, "a") as f:
            for lemma in new_base_vocab:
                f.write(f"{lemma}\n")
            f.write("\n")

    def parse_into_db(
        self,
        content_path: str,
        metadata_path: str,
    ):
        """
        TODO
        """
        existing_base_vocab = self._load_vocab(Const.PATH_BASE_VOCAB)
        existing_irrelevant_vocab = self._load_vocab(Const.PATH_BASE_VOCAB)

        source_metadata = self._load_metadata(metadata_path)

        source_kind_id = self.api.post_source_kind(source_metadata.source_kind)
        source_id = self.api.post_source(
            title=source_metadata.title, source_kind_id=source_kind_id
        )
        status_id_pending = self.api.post_status(StatusVal.PENDING)

        content_line_num = buf_count_newlines(content_path)

        with self.nlp_parsing_pipes, open(content_path) as f, Progress() as p:
            task = p.add_task(
                "[yellow]Parsing into database", total=content_line_num
            )

            raw_context = " "
            while raw_context:
                # if raw_context != " ":
                p.advance(task, Const.CONTEXT_LINE_NUM)

                raw_context = " ".join(
                    [
                        line.strip()
                        for line in islice(f, Const.CONTEXT_LINE_NUM)
                    ]
                )

                doc_complete = self.nlp(raw_context)

                doc_filtered = list(
                    filter(
                        lambda t: self._is_relevant_token(
                            t,
                            existing_base_vocab,
                            existing_irrelevant_vocab,
                        ),
                        doc_complete,
                    )
                )

                if not doc_filtered:
                    continue

                db_data = {
                    t.text: IntermediaryDbDatum(
                        lemma := t.lemma_.lower(),
                        self.api.post_lemma(lemma, status_id_pending),
                        t.tag_,
                        UposTag(t.pos_),
                    )
                    for t in doc_filtered
                }

                context_value = self._construct_context_value(
                    doc_complete, db_data
                )
                context_id = self.api.post_context(context_value, source_id)

                for datum in db_data.values():
                    self.api.post_lemma_source_relation(
                        datum.lemma_id, source_id
                    )
                    self.api.post_lemma_context_relation(
                        datum.lemma_id, context_id, datum.pos, datum.tag
                    )

    def _customise_tokenisation(self):
        prefixes = self.nlp.Defaults.prefixes + [r"""^-+"""]  # type: ignore
        prefix_regex = spacy.util.compile_prefix_regex(prefixes)
        self.nlp.tokenizer.prefix_search = prefix_regex.search

        suffixes = self.nlp.Defaults.suffixes + [
            r"""-+$""",
        ]  # type: ignore
        suffix_regex = spacy.util.compile_suffix_regex(suffixes)
        self.nlp.tokenizer.suffix_search = suffix_regex.search

    @staticmethod
    def _load_metadata(path: str) -> SourceMetadata:
        with open(path) as f:
            metadata = json.load(f)
        return SourceMetadata(**metadata)

    @staticmethod
    def _load_vocab(path: str) -> set[str]:
        with open(path) as f:
            vocab = set(f.read().split())
        return vocab

    @staticmethod
    def _is_relevant_token(
        token: Token, base_vocab: set[str], irrelevant_vocab: set[str]
    ):
        lemma = token.lemma_.lower()
        return (
            lemma not in base_vocab
            and lemma not in irrelevant_vocab
            and token.pos_ in Const.UPOS_RELEVANT
            and not token.is_stop
            and not token.like_num
            and not token.is_space
            and not token.is_digit
            and token.is_alpha
        )

    @staticmethod
    def _construct_context_value(
        doc: Doc, db_data: dict[str, IntermediaryDbDatum]
    ) -> str:
        context_value = []

        for t in doc:
            if (token := t.text) in db_data:
                context_value.append(
                    f"{token}::{db_data[token].lemma_id}{t.whitespace_}"
                )
            else:
                context_value.append(f"{token}{t.whitespace_}")

        return json.dumps(context_value)


if __name__ == "__main__":
    tp = TextParser(ApiEnvironment.DEV)
    tp.parse_into_db(
        "assets/dev-samples/harry-potter.content.txt",
        "assets/dev-samples/harry-potter.meta.json",
    )
    # tp.parse_into_base_vocab("assets/dev-samples/harry-potter.content.txt")
