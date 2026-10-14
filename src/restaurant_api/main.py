from fastapi import FastAPI

app = FastAPI(title="Restaurant API")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Restaurant API!"}