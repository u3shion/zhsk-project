import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
SERVICE_KEY = os.getenv("SERVICE_KEY", "")
USERS_SERVICE_URL = os.getenv("USERS_SERVICE_URL", "http://users:8000")
