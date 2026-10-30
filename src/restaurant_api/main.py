from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import FRONTEND_URL
from .router.router import router as menu_router
from .router.order_router import router as order_router
from .router.table_router import router as table_router
from .router.auth_router import router as auth_router


app = FastAPI(title="Restaurant API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", FRONTEND_URL],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(menu_router)
app.include_router(table_router, prefix="/api")
app.include_router(order_router)
app.include_router(auth_router)


@app.get("/")
def read_root():
    return {"message": "Welcome to the Restaurant API!"}