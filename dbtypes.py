"""
TODO
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


class Environment(Enum):
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

    PENDING = "pending"
    ACCEPTED = "accepted"


class ConfiguredBaseModel(BaseModel):
    class Config:
        use_enum_values = False

    def to_dict(self):
        data = self.dict()
        updated = {
            k: v.isoformat()
            for k, v in data.items()
            if isinstance(v, datetime)
        }
        data.update(updated)
        return data


class SourceKind(ConfiguredBaseModel):
    id: SourceKindId = SourceKindId(-1)
    kind: SourceKindVal


class Source(ConfiguredBaseModel):
    id: SourceId = SourceId(-1)
    title: str
    source_kind_id: SourceKindId


class Status(ConfiguredBaseModel):
    id: StatusId = StatusId(-1)
    status: StatusVal


class Lemma(ConfiguredBaseModel):
    id: LemmaId = LemmaId(-1)
    lemma: str
    created: datetime = datetime(1970, 1, 1)
    status_id: StatusId


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
