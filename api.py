"""
API
===
Exposes endpoints to interact with the database.
"""

from typing import TypedDict

from fastapi import FastAPI
from pydantic import BaseModel

from db import LexDbIntegrator
from dbtypes import Environment, Lemma, LemmaId

db = LexDbIntegrator(Environment.DEV)
app = FastAPI()


class EmptyDict(TypedDict, total=False):
    pass


class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None


@app.get("/")
def read_root():
    return {"api_status": "working"}


@app.get("/lemma/get_lemma/{lemma_id}")
def get_lemma(lemma_id: LemmaId) -> Lemma | EmptyDict:
    return db.get_lemma(lemma_id) or EmptyDict()


# @app.get("/lemma/get_lemma_id/{lemma}")
# def get_lemma_id(lemma: str) -> LemmaId:
#     return db.get_lemma_id(lemma)


@app.post("/lemma/add_lemma")
def add_lemma(lemma: Lemma) -> LemmaId:
    return db.add_lemma(lemma)


@app.get("/items/{item_id}")
async def create_item(item_id: int, item: Item):
    return {"item_id": item_id, **item.dict()}
