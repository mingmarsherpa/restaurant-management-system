from fastapi import FastAPI

from .router.router import router as menu_router


app = FastAPI(title="Restaurant API")
app.include_router(menu_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Restaurant API!"}