from fastapi import FastAPI

app = FastAPI()


@app.get("/api/test")
async def hello_world():
    return {"messsage": "hello world"}
