from fastapi import FastAPI
from pydantic import BaseModel

from ._const import Const


class T(BaseModel):
    pass


app = FastAPI()


@app.get("/api/python")
async def hello_world():
    return {"messsage": "hello python"}


@app.get("/haskell")
async def hello_haskell():
    return {"messsage": "hello haskell"}


@app.get("/relative")
async def relative_import_two():
    return {"messsage": Const.UPOS_RELEVANT.pop()}
