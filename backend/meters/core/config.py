import os

from dotenv import load_dotenv


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
SERVICE_KEY = os.getenv("SERVICE_KEY", "internal-service-key")

EXTERNAL_SERVICE_URL = os.getenv("EXTERNAL_SERVICE_URL", "http://localhost:8004")
EXTERNAL_SERVICE_PROVIDER_ID = os.getenv("EXTERNAL_SERVICE_PROVIDER_ID", "ZHSK-32")
EXTERNAL_SERVICE_PROVIDER_NAME = os.getenv("EXTERNAL_SERVICE_PROVIDER_NAME", "ЖСК-32")
