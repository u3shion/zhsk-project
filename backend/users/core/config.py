import os

from dotenv import load_dotenv


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_SECRET = os.getenv("ADMIN_SECRET")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
SERVICE_KEY = os.getenv("SERVICE_KEY", "internal-service-key")
