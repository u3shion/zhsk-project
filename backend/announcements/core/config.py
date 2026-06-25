import os

from dotenv import load_dotenv


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")

# MinIO
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "announcements-photos")
MINIO_PUBLIC_URL = os.getenv("MINIO_PUBLIC_URL", "http://localhost:9000")
