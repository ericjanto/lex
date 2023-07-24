from fastapi import FastAPI

from ._const import Const
from ._otherfile import hi

app = FastAPI()


@app.get("/api/python")
async def hello_world():
    return {"messsage": "hello python"}


@app.get("/haskell")
async def hello_haskell():
    return {"messsage": "hello haskell"}


@app.get("/relative")
async def relative_import():
    return {"messsage": hi()}


@app.get("/relative-two")
async def relative_import_two():
    return {"messsage": Const.UPOS_RELEVANT.pop()}
