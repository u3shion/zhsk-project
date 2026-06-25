import io
import uuid
from pathlib import PurePosixPath

from minio import Minio
from minio.error import S3Error

from core.config import MINIO_ACCESS_KEY, MINIO_BUCKET, MINIO_ENDPOINT, MINIO_PUBLIC_URL, MINIO_SECRET_KEY


def _client() -> Minio:
    return Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False,
    )


def upload_photo(file_content: bytes, filename: str, content_type: str) -> str:
    ext = PurePosixPath(filename).suffix.lower()
    object_name = f"{uuid.uuid4().hex}{ext}"

    client = _client()
    client.put_object(
        bucket_name=MINIO_BUCKET,
        object_name=object_name,
        data=io.BytesIO(file_content),
        length=len(file_content),
        content_type=content_type,
    )

    return f"{MINIO_PUBLIC_URL}/{MINIO_BUCKET}/{object_name}"


def delete_photo(object_name: str) -> bool:
    name = PurePosixPath(object_name).name
    try:
        _client().remove_object(MINIO_BUCKET, name)
        return True
    except S3Error:
        return False
