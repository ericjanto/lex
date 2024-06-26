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
from spacy.lang.en.stop_words import (
    STOP_WORDS,  # TODO @ej localisation-relevant
)
from spacy.lang.lex_attrs import is_stop
from spacy.tokens import Doc, Token

from api._const import Const
from api._dbtypes import (
    LemmaContextRelation,
    LemmaId,
    LemmaSourceRelation,
    SourceMetadata,
    StatusVal,
    UposTag,
)
from api._utils import buf_count_newlines, enhanced_progress_params

from .apirequestor import ApiRequestor


class IntermediaryDbDatum(NamedTuple):
    lemma: str
    lemma_id: LemmaId
    tag: str
    pos: UposTag


class TextParser:
    """
    Parsing class which extracts vocabulary from text.
    """

    def __init__(self) -> None:
        """
        TODO

        - passing some shared args to self.parse instead of
          creating class members as nlp load time is long, and
          this allows us to reuse the same instance for parsing of
          multiple documents
        """
        self.api = ApiRequestor()

        self.nlp = en_core_web_trf.load()  # TODO @ej localisation-relevant
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

        with self.nlp_parsing_pipes, open(content_path) as f, Progress(
            *enhanced_progress_params()
        ) as p:
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
        existing_irrelevant_vocab = self._load_vocab(
            Const.PATH_IRRELEVANT_VOCAB
        )

        source_metadata = self._load_metadata(metadata_path)

        source_kind_id = self.api.post_source_kind(source_metadata.source_kind)
        source_id = self.api.post_source(
            title=source_metadata.title,
            source_kind_id=source_kind_id,
            author=source_metadata.author,
            lang=source_metadata.language,
        )
        status_id_staged = self.api.post_status(StatusVal.STAGED)

        self._normalise_file(content_path)
        content_line_num = buf_count_newlines(content_path)
        with self.nlp_parsing_pipes, open(content_path) as f, Progress(
            *enhanced_progress_params()
        ) as p:
            task = p.add_task(
                "[yellow]Parsing into database", total=content_line_num
            )

            # TODO: [perf] further batch requests (e.g. 1000 lemmata at a time,
            #              not in every batch loop)
            raw_context = []
            pre_spill = []
            post_spill = []
            while True:
                p.advance(task, Const.CONTEXT_LINE_NUM)

                if not post_spill:
                    raw_context = [
                        line.strip()
                        for line in islice(f, Const.CONTEXT_LINE_NUM)
                    ]
                else:
                    raw_context = post_spill + [
                        line.strip()
                        for line in islice(
                            f, Const.CONTEXT_LINE_NUM - Const.SPILL_LINE_NUM
                        )
                    ]

                if not raw_context:
                    break

                post_spill = [
                    line.strip() for line in islice(f, Const.SPILL_LINE_NUM)
                ]

                spilled_context = " ".join(
                    pre_spill + raw_context + post_spill
                )

                doc_spilled = self.nlp(spilled_context)

                # TODO: only tokenise, don't use all the other pipes
                pre_spill_len = len(self.nlp(" ".join(pre_spill)))
                post_spill_len = len(self.nlp(" ".join(post_spill)))

                if raw_context and len(raw_context) >= Const.SPILL_LINE_NUM:
                    pre_spill = [raw_context[-Const.SPILL_LINE_NUM]]
                elif raw_context:
                    pre_spill = raw_context
                else:
                    pre_spill = []

                doc_context = doc_spilled[
                    pre_spill_len : len(doc_spilled) - post_spill_len
                ]

                doc_filtered = list(
                    filter(
                        lambda t: self._is_relevant_token(
                            t,
                            existing_base_vocab,
                            existing_irrelevant_vocab,
                        ),
                        doc_context,
                    )
                )

                if not doc_filtered:
                    context_value = self._construct_context_value(
                        doc_context, {}
                    )
                    self.api.post_context(context_value, source_id)
                    continue

                # TODO: I think spacy lowers lemma text by default
                lemmata_values = [t.lemma_.lower() for t in doc_filtered]

                self.api.bulk_post_lemmata(
                    lemmata_values=lemmata_values,
                    status_id=status_id_staged,
                    source_id=source_id,
                )

                lemma_id_dict = self.api.bulk_get_lemma_id_dict(lemmata_values)

                db_data = {
                    t.text: IntermediaryDbDatum(
                        lemma := t.lemma_.lower(),
                        lemma_id_dict[lemma],
                        t.tag_,
                        UposTag(t.pos_),
                    )
                    for t in doc_filtered
                }

                context_value = self._construct_context_value(
                    doc_context, db_data
                )
                context_id = self.api.post_context(context_value, source_id)

                source_rels = []
                context_rels = []
                for datum in db_data.values():
                    source_rels.append(
                        LemmaSourceRelation(
                            lemma_id=datum.lemma_id, source_id=source_id
                        )
                    )
                    context_rels.append(
                        LemmaContextRelation(
                            lemma_id=datum.lemma_id,
                            context_id=context_id,
                            upos_tag=datum.pos,
                            detailed_tag=datum.tag,
                        )
                    )

                self.api.bulk_post_lemma_source_relations(source_rels)
                self.api.bulk_post_lemma_context_relations(context_rels)

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
            and not is_stop(lemma, STOP_WORDS)
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

    @staticmethod
    def _normalise_file(path: str):
        wrapped_lines = []
        min_length = 60
        max_length = 80
        with open(path) as f:
            borrowed = ""
            for i, line in enumerate(f):
                bline = f"{borrowed} {line.rstrip()}".lstrip()

                if len(bline) == 0 and i != 0:
                    continue

                if len(bline) < min_length:
                    borrowed = bline
                    continue

                if len(bline) <= max_length:
                    wrapped_lines.append(f"{bline}\n")
                    borrowed = ""
                    continue

                break_point = bline.rfind(" ", 0, max_length - 1)
                if break_point == -1:
                    break_point = max_length
                wrapped_lines.append(f"{bline[:break_point]}\n")
                borrowed = bline[break_point:].lstrip()

            while borrowed:
                if len(borrowed) <= max_length:
                    wrapped_lines.append(f"{borrowed}\n")
                    borrowed = ""
                else:
                    break_point = borrowed.rfind(" ", 0, max_length - 1)
                    if break_point == -1:
                        break_point = max_length
                    wrapped_lines.append(f"{borrowed[:break_point]}\n")
                    borrowed = borrowed[break_point:].lstrip()

        with open(path, "w") as f:
            f.writelines(wrapped_lines)


if __name__ == "__main__":
    tp = TextParser()
    tp.parse_into_db(
        "assets/dev-samples/harry-potter.content.txt",
        "assets/dev-samples/harry-potter.meta.json",
    )
    # tp.parse_into_base_vocab("assets/dev-samples/harry-potter.content.txt")
