from fastapi import FastAPI

app = FastAPI()


@app.get("/api/python")
async def hello_world():
    return {"messsage": "hello python"}


@app.get("/haskell")
async def hello_haskell():
    return {"messsage": "hello haskell"}
