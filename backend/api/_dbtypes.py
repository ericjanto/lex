"""
Typing class for the database integration.
"""
from datetime import datetime
from enum import Enum
from typing import NewType

from pydantic import BaseModel

SourceKindId = NewType("SourceKindId", int)
SourceId = NewType("SourceId", int)
StatusId = NewType("StatusId", int)
LemmaId = NewType("LemmaId", int)
LemmaSourceId = NewType("LemmaSourceId", int)
ContextId = NewType("ContextId", int)
LemmaContextId = NewType("LemmaContextId", int)


class DbEnvironment(Enum):
    """
    Represents the environment of the database.
    """

    PROD = "PROD"
    DEV = "DEV"
    DEVADMIN = "DEVADMIN"


class SourceKindVal(Enum):
    """
    Represents a source kind.
    """

    BOOK = "book"
    ARTICLE = "article"
    CONVERSATION = "conversation"
    FILM = "film"
    OTHER = "other"


class UposTag(Enum):
    """
    Represents a universal part of speech tag.
    """

    NOUN = "NOUN"
    VERB = "VERB"
    ADJ = "ADJ"
    ADV = "ADV"
    PROPN = "PROPN"
    PRON = "PRON"
    DET = "DET"
    ADP = "ADP"
    NUM = "NUM"
    CONJ = "CONJ"
    PRT = "PRT"
    PUNCT = "PUNCT"
    X = "X"


class StatusVal(Enum):
    """
    Represents a lemma status.
    """

    STAGED = "staged"
    COMMITTED = "committed"
    PUSHED = "pushed"


class ConfiguredBaseModel(BaseModel):
    def to_dict(self):
        data = self.dict()

        update_dates = {
            k: v.isoformat()
            for k, v in data.items()
            if isinstance(v, datetime)
        }

        update_enums = {
            k: v.value for k, v in data.items() if isinstance(v, Enum)
        }
        data.update(update_dates)
        data.update(update_enums)
        return data


class SourceKind(ConfiguredBaseModel):
    id: SourceKindId = SourceKindId(-1)
    kind: SourceKindVal


class Source(ConfiguredBaseModel):
    id: SourceId = SourceId(-1)
    title: str
    source_kind_id: SourceKindId
    author: str
    lang: str
    removed_lemmata_num: int = 0


class SourceMetadata(ConfiguredBaseModel):
    author: str
    title: str
    language: str
    source_kind: SourceKindVal


class Status(ConfiguredBaseModel):
    id: StatusId = StatusId(-1)
    status: StatusVal


class Lemma(ConfiguredBaseModel):
    id: LemmaId = LemmaId(-1)
    lemma: str
    created: datetime = datetime(1970, 1, 1)
    status_id: StatusId
    found_in_source: SourceId


class LemmaList(ConfiguredBaseModel):
    lemmata: list[Lemma]

    def to_dict(self):
        return {"lemmata": [lemma.to_dict() for lemma in self.lemmata]}


class LemmaSourceRelation(ConfiguredBaseModel):
    id: LemmaSourceId = LemmaSourceId(-1)
    lemma_id: LemmaId
    source_id: SourceId


class Context(ConfiguredBaseModel):
    id: ContextId = ContextId(-1)
    context_value: str
    created: datetime = datetime(1970, 1, 1)
    source_id: SourceId


class LemmaContextRelation(ConfiguredBaseModel):
    id: LemmaContextId = LemmaContextId(-1)
    lemma_id: LemmaId
    context_id: ContextId
    upos_tag: UposTag
    detailed_tag: str
