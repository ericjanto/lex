"""
API
===
Exposes endpoints to interact with the database.
"""

import os
from typing import TypedDict, Union

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rich import print as rprint

from ._db import LexDbIntegrator
from ._dbtypes import (
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
)

origins = ["*"]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


def set_db_env(env: DbEnvironment):
    global db
    rprint(f"[green]Connected to {env.value} database branch.")
    db = LexDbIntegrator(env)


if os.environ.get("VERCEL"):
    set_db_env(DbEnvironment.PROD)
else:
    set_db_env(DbEnvironment.DEV)


class EmptyDict(TypedDict, total=False):
    pass


class LemmaValue(BaseModel):
    value: str


@app.get("/api_status")
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
