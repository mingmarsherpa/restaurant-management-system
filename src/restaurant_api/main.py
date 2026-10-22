from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .router.router import router as menu_router


app = FastAPI(title="Restaurant API")
app.add_middleware(
	CORSMiddleware,
	allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
	allow_credentials=False,
	allow_methods=["*"],
	allow_headers=["*"],
)
app.include_router(menu_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Restaurant API!"}