import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
LAN_HOST = os.getenv("LAN_HOST", "localhost")
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "5173"))
API_PORT = int(os.getenv("API_PORT", "8000"))
FRONTEND_URL = f"http://{LAN_HOST}:{FRONTEND_PORT}"
API_URL = f"http://{LAN_HOST}:{API_PORT}"
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
)

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")