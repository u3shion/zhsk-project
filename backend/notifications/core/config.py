import os

from dotenv import load_dotenv


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
SERVICE_KEY = os.getenv("SERVICE_KEY", "internal-service-key")

USERS_SERVICE_URL = os.getenv("USERS_SERVICE_URL", "http://localhost:8001")
METERS_SERVICE_URL = os.getenv("METERS_SERVICE_URL", "http://localhost:8002")

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "ЖСК <noreply@example.com>")
