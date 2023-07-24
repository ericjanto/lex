"""
API
===
Exposes endpoints to interact with the database.
"""

import os
from enum import Enum
from typing import TypedDict, Union

import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rich import print as rprint

from const import Const
from db import LexDbIntegrator
from dbtypes import (
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
    SourceKind,
    SourceKindId,
    SourceKindVal,
    Status,
    StatusId,
    StatusVal,
    UposTag,
)

origins = ["*"]
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def set_db_env(env: DbEnvironment):
    global db
    rprint(f"[green]Connecting to {env.value} database branch.")
    db = LexDbIntegrator(env)


if "gunicorn" in os.environ.get("SERVER_SOFTWARE", ""):
    set_db_env(DbEnvironment.DEV)  # TODO @ej verify this before deploying
else:
    set_db_env(DbEnvironment.DEV)


class ApiEnvironment(str, Enum):
    PROD = "PROD"
    DEV = "DEV"


class EmptyDict(TypedDict, total=False):
    pass


class LemmaValue(BaseModel):
    value: str


@app.get("/")
async def read_root():
    return {"api_status": "working"}


@app.get("/lemma/{lemma_id}")
async def get_lemma(lemma_id: LemmaId) -> Union[Lemma, EmptyDict]:
    return db.get_lemma(lemma_id) or EmptyDict()


@app.get("/lemma_id")
async def get_lemma_id(lemma: LemmaValue) -> LemmaId:
    return db.get_lemma_id(lemma.value)


@app.get("/lemma_status/{status_val}")
async def get_status_id(status_val: StatusVal) -> StatusId:
    return db.get_status_id(status_val)


@app.get("/lemma_status_by_id/{status_id}")
async def get_status_by_id(status_id: StatusId) -> Union[Status, None]:
    return db.get_status_by_id(status_id)


@app.get("/status_lemmata")
async def get_status_lemma_rows(
    status_val: StatusVal,
    page: Union[int, None],
    page_size: Union[int, None] = None,
) -> list[Lemma]:
    return db.get_status_lemma_rows(
        status_val=status_val, page=page, page_size=page_size
    )


@app.get("/status_lemmata_table")
async def get_status_lemma_rows_table(
    status_val: StatusVal,
    page: Union[int, None],
    page_size: Union[int, None] = None,
) -> str:
    return db.get_status_lemma_rows_table(
        status_val=status_val, page=page, page_size=page_size
    )


@app.get("/contexts")
async def get_paginated_contexts(page: int, page_size: int) -> list[Context]:
    return db.get_paginated_contexts(page, page_size)


@app.get("/lemma_contexts/{lemma_id}")
async def get_lemma_contexts(
    lemma_id: LemmaId, page: int, page_size: int
) -> list[Context]:
    return db.get_lemma_contexts(lemma_id, page, page_size)


@app.get("/sources")
async def get_sources(
    page: int,
    page_size: int,
    author: Union[str, None] = None,
    lang: Union[str, None] = None,
    source_kind_id: Union[SourceKindId, None] = None,
) -> list[Source]:
    args = locals()
    filter_params = {
        k: v
        for k, v in args.items()
        if v is not None and k not in ["page", "page_size"]
    } or None

    return db.get_paginated_sources(page, page_size, filter_params)


@app.get("/source/{source_id}")
async def get_source(source_id: SourceId) -> Union[Source, None]:
    return db.get_source(source_id)


@app.get("/source_kind/{source_kind_id}")
async def get_source_kind(
    source_kind_id: SourceKindId,
) -> Union[SourceKind, None]:
    return db.get_source_kind(source_kind_id)


@app.get("/source_contexts/{source_id}")
async def get_source_contexts(
    source_id: SourceId, page: int, page_size: int
) -> list[Context]:
    return db.get_paginated_source_contexts(source_id, page, page_size)


@app.post("/lemma")
async def post_lemma(lemma: Lemma) -> LemmaId:
    return db.add_lemma(lemma)


@app.post("/lemma_status")
async def post_status(status_val: StatusVal) -> StatusId:
    return db.add_status(status_val)


@app.post("/lemma_source")
async def post_lemma_source_relation(
    lemma_source_relation: LemmaSourceRelation,
) -> LemmaSourceId:
    return db.add_lemma_source_relation(lemma_source_relation)


@app.post("/source_kind")
async def post_source_kind(source_kind_val: SourceKindVal) -> SourceKindId:
    return db.add_source_kind(source_kind_val)


@app.post("/source")
async def post_source(source: Source) -> SourceId:
    return db.add_source(source)


@app.post("/context")
async def post_context(context: Context) -> ContextId:
    return db.add_context(context)


@app.post("/lemma_context")
async def post_lemma_context_relation(
    lemma_context_relation: LemmaContextRelation,
) -> LemmaContextId:
    return db.add_lemma_context_relation(lemma_context_relation)


@app.delete("/lemma")
async def delete_lemma(lemma_ids: list[LemmaId]):
    return all(db.delete_lemma(lid) for lid in lemma_ids)


@app.patch("/status")
async def update_status(lemma_ids: list[LemmaId], new_status_id: StatusId):
    return db.update_lemmata_status(lemma_ids, new_status_id)


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

    def get_lemma_name(self, lemma_id: LemmaId) -> str:
        r = requests.get(f"{self.api_url}/lemma/{lemma_id}")
        return Lemma(**dict(r.json())).lemma if r.status_code == 200 else ""

    def get_lemma_id(self, lemma: str) -> LemmaId:
        r = requests.get(
            f"{self.api_url}/lemma_id", json=LemmaValue(value=lemma).dict()
        )
        return LemmaId(r.json()) if r.status_code == 200 else LemmaId(-1)

    def get_lemma_status(self, status_val: StatusVal) -> StatusId:
        r = requests.get(f"{self.api_url}/lemma_status/{status_val.value}")
        assert r.status_code == 200
        return StatusId(r.json())

    def get_status_lemmata(
        self,
        status_val: StatusVal,
        page: Union[int, None] = None,
        page_size: Union[int, None] = None,
        table: bool = False,
    ) -> str:
        query_params = {}
        # Add page and page_size query params if provided
        if page:
            query_params["page"] = page
        if page_size:
            query_params["page_size"] = page_size
        query_params["status_val"] = status_val.value
        r = requests.get(
            f"{self.api_url}/status_lemmata{'_table' if table else ''}",
            params=query_params,
        )
        assert r.status_code == 200
        return r.json()

    def post_lemma(
        self, lemma: str, status_id: StatusId, source_id: SourceId
    ) -> LemmaId:
        r = requests.post(
            f"{self.api_url}/lemma",
            json=Lemma(
                lemma=lemma, status_id=status_id, found_in_source=source_id
            ).to_dict(),
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
        self, title: str, source_kind_id: SourceKindId, author: str, lang: str
    ) -> SourceId:
        r = requests.post(
            f"{self.api_url}/source",
            json=Source(
                title=title,
                source_kind_id=source_kind_id,
                author=author,
                lang=lang,
            ).to_dict(),
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

    def delete_lemmata(self, lemma_ids: set[LemmaId]) -> bool:
        r = requests.delete(f"{self.api_url}/lemma", json=list(lemma_ids))
        assert r.status_code == 200
        return r.json()

    def update_multiple_status(
        self, lemma_ids: set[LemmaId], new_status_id: StatusId
    ) -> bool:
        r = requests.patch(
            f"{self.api_url}/status?new_status_id={new_status_id}",
            json=list(lemma_ids),
        )
        assert r.status_code == 200
        return r.json()
