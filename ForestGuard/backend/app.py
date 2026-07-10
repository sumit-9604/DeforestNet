# pyrefly: ignore [missing-import]
from fastapi import FastAPI

app = FastAPI(title="ForestGuard API")

@app.get("/")
def read_root():
    return {"message": "Welcome to ForestGuard API"}
