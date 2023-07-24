import os
from typing import TypedDict, Union

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from rich import print as rprint

from ._const import Const
from ._db import Lemma, LemmaId, LexDbIntegrator
from ._dbtypes import DbEnvironment

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


if os.environ.get("VERCEL"):
    set_db_env(DbEnvironment.DEV)
else:
    set_db_env(DbEnvironment.DEV)


class EmptyDict(TypedDict, total=False):
    pass


@app.get("/lemma/{lemma_id}")
async def get_lemma(lemma_id: LemmaId) -> Union[Lemma, EmptyDict]:
    return db.get_lemma(lemma_id) or EmptyDict()


@app.get("/api/python")
async def hello_world():
    return {"messsage": "hello python"}


@app.get("/haskell")
async def hello_haskell():
    return {"messsage": "hello haskell"}


@app.get("/relative")
async def relative_import_two():
    return {"messsage": Const.UPOS_RELEVANT.pop()}
