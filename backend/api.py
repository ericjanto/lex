"""
API
===
Exposes endpoints to interact with the database.
"""

from enum import Enum
from typing import TypedDict, Union

import requests
from fastapi import FastAPI
from pydantic import BaseModel

from backend.const import Const
from backend.db import LexDbIntegrator
from backend.dbtypes import (
    Context,
    ContextId,
    DbEnvironment,
    Lemma,
    LemmaContextId,
    LemmaContextRelation,
    LemmaId,
    LemmaSourceId,
    LemmaSourceRelation,
    Source,
    SourceId,
    SourceKindId,
    SourceKindVal,
    StatusId,
    StatusVal,
    UposTag,
)

db = LexDbIntegrator(DbEnvironment.DEV)  # TODO: can this be settable?
app = FastAPI()


class ApiEnvironment(str, Enum):
    PROD = "PROD"
    DEV = "DEV"


class EmptyDict(TypedDict, total=False):
    pass


class LemmaValue(BaseModel):
    value: str


@app.get("/")
def read_root():
    return {"api_status": "working"}


@app.get("/lemma/{lemma_id}")
def get_lemma(lemma_id: LemmaId) -> Union[Lemma, EmptyDict]:
    return db.get_lemma(lemma_id) or EmptyDict()


@app.get("/lemma_id")
def get_lemma_id(lemma: LemmaValue) -> LemmaId:
    return db.get_lemma_id(lemma.value)


@app.get("/lemma_status/{status_val}")
def get_status_id(status_val: StatusVal) -> StatusId:
    return db.get_status_id(status_val)


@app.get("/pending")
def get_pending_lemma_rows(head: Union[int, None] = None) -> str:
    return db.get_pending_lemma_rows(head=head)


@app.post("/lemma")
def post_lemma(lemma: Lemma) -> LemmaId:
    return db.add_lemma(lemma)


@app.post("/lemma_status")
def post_status(status_val: StatusVal) -> StatusId:
    return db.add_status(status_val)


@app.post("/lemma_source")
def post_lemma_source_relation(
    lemma_source_relation: LemmaSourceRelation,
) -> LemmaSourceId:
    return db.add_lemma_source_relation(lemma_source_relation)


@app.post("/source_kind")
def post_source_kind(source_kind_val: SourceKindVal) -> SourceKindId:
    return db.add_source_kind(source_kind_val)


@app.post("/source")
def post_source(source: Source) -> SourceId:
    return db.add_source(source)


@app.post("/context")
def post_context(context: Context) -> ContextId:
    return db.add_context(context)


@app.post("/lemma_context")
def post_lemma_context_relation(
    lemma_context_relation: LemmaContextRelation,
) -> LemmaContextId:
    return db.add_lemma_context_relation(lemma_context_relation)


@app.delete("/lemma/{lemma_id}")
def delete_lemma(lemma_id: LemmaId):
    return db.delete_lemma(lemma_id)


@app.patch("/status/{lemma_id}")
def update_status(lemma_id: LemmaId, new_status_id: StatusId):
    return db.update_lemma_status(lemma_id, new_status_id)


class ApiRequestor:
    """
    Encapsulation class for sending HTTP requests to the api.
    """

    def __init__(self, api_env: ApiEnvironment) -> None:
        """
        Args:
            env: api environment (dev or prod) to interact with
        """
        if api_env == ApiEnvironment.DEV:
            self.api_url = Const.API_DEV_URL
        else:
            raise NotImplementedError

    def get_lemma_id(self, lemma: str) -> LemmaId:
        r = requests.get(
            f"{self.api_url}/lemma_id", json=LemmaValue(value=lemma).dict()
        )
        return LemmaId(r.json()) if r.status_code == 200 else LemmaId(-1)

    def get_lemma_status(self, status_val: StatusVal) -> StatusId:
        r = requests.get(f"{self.api_url}/lemma_status/{status_val.value}")
        assert r.status_code == 200
        return StatusId(r.json())

    def get_pending_lemma_rows(self, head: Union[int, None] = None) -> str:
        r = requests.get(
            f"{self.api_url}/pending{f'?head={head}' if head else ''}"
        )
        assert r.status_code == 200
        return r.json()

    def post_lemma(self, lemma: str, status_id: StatusId) -> LemmaId:
        r = requests.post(
            f"{self.api_url}/lemma",
            json=Lemma(lemma=lemma, status_id=status_id).to_dict(),
        )
        assert r.status_code == 200
        assert (lid := LemmaId(r.json())) != -1
        return lid

    def post_status(self, status_val: StatusVal) -> StatusId:
        r = requests.post(
            f"{self.api_url}/lemma_status?status_val={status_val.value}",
        )
        assert r.status_code == 200
        assert (sid := StatusId(r.json())) != -1
        return sid

    def post_source_kind(self, source_kind_val: SourceKindVal) -> SourceKindId:
        r = requests.post(
            f"{self.api_url}/source_kind?source_kind_val={source_kind_val.value}",
        )
        assert r.status_code == 200
        assert (skid := SourceKindId(r.json())) != -1
        return skid

    def post_source(
        self, title: str, source_kind_id: SourceKindId
    ) -> SourceId:
        r = requests.post(
            f"{self.api_url}/source",
            json=Source(title=title, source_kind_id=source_kind_id).to_dict(),
        )
        assert r.status_code == 200
        assert (sid := SourceId(r.json())) != -1
        return sid

    def post_context(
        self, context_value: str, source_id: SourceId
    ) -> ContextId:
        r = requests.post(
            f"{self.api_url}/context",
            json=Context(
                context_value=context_value, source_id=source_id
            ).to_dict(),
        )
        assert r.status_code == 200
        assert (cid := ContextId(r.json())) != -1
        return cid

    def post_lemma_context_relation(
        self,
        lemma_id: LemmaId,
        context_id: ContextId,
        upos_tag: UposTag,
        detailed_tag: str,
    ) -> LemmaContextId:
        r = requests.post(
            f"{self.api_url}/lemma_context",
            json=LemmaContextRelation(
                lemma_id=lemma_id,
                context_id=context_id,
                upos_tag=upos_tag,
                detailed_tag=detailed_tag,
            ).to_dict(),
        )
        assert r.status_code == 200
        assert (lcid := LemmaContextId(r.json())) != -1
        return lcid

    def post_lemma_source_relation(
        self,
        lemma_id: LemmaId,
        source_id: SourceId,
    ) -> LemmaSourceId:
        r = requests.post(
            f"{self.api_url}/lemma_source",
            json=LemmaSourceRelation(
                lemma_id=lemma_id, source_id=source_id
            ).to_dict(),
        )
        assert r.status_code == 200
        assert (lsid := LemmaSourceId(r.json())) != -1
        return lsid

    def delete_lemma(self, lemma_id: LemmaId) -> bool:
        r = requests.delete(f"{self.api_url}/lemma/{lemma_id}")
        assert r.status_code == 200
        return r.json()

    def update_status(
        self, lemma_id: LemmaId, new_status_id: StatusId
    ) -> bool:
        r = requests.patch(
            f"{self.api_url}/status/{lemma_id}?new_status_id={new_status_id}"
        )
        assert r.status_code == 200
        return r.json()
