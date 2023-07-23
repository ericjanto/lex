from backend.utils import relativy_path
from fastapi import FastAPI

app = FastAPI()


@app.get("/api/python")
def hello_world():
    return {"message": "Hello World"}


@app.get("/api/import")
def import_test():
    return {"message": relativy_path("he!")}
