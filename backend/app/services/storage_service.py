import os
import tempfile
from typing import Optional

from app.core.config import settings
from app.core.minio_versioning import (
    get_client,
    enable_versioning,
    upload_file as core_upload_file,
    list_versions as core_list_versions,
    download_file as core_download_file,
)

# Initialize MinIO Client
client = get_client()

# Auto-initialize bucket and versioning configuration on startup
try:
    if not client.bucket_exists(settings.MINIO_BUCKET_NAME):
        client.make_bucket(settings.MINIO_BUCKET_NAME)
    enable_versioning(client, settings.MINIO_BUCKET_NAME)
except Exception as e:
    print(f"[-] Failed to auto-initialize MinIO bucket or versioning: {e}")


def upload_file(file_bytes: bytes, filename: str) -> str:
    """
    Upload a file from bytes to MinIO and return the object ID (filename).

    This function wraps the core upload logic by saving the bytes to a temporary
    file, uploading it to MinIO via the core fput function, and then cleaning up.

    Parameters:
    - file_bytes (bytes): The raw file contents in bytes.
    - filename (str): The name/path of the object in the MinIO bucket.

    Returns:
    - str: The object ID (filename) of the uploaded file.
    """
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(file_bytes)
        temp_path = temp_file.name

    try:
        core_upload_file(
            client=client,
            bucket_name=settings.MINIO_BUCKET_NAME,
            local_path=temp_path,
            object_name=filename,
        )
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return filename


def list_versions(object_id: str) -> list:
    """
    List all version IDs of the specified object ID (filename) in MinIO.

    Parameters:
    - object_id (str): The object ID (filename) to check.

    Returns:
    - list: A list of version IDs representing the version history.
    """
    return core_list_versions(
        client=client,
        bucket_name=settings.MINIO_BUCKET_NAME,
        object_name=object_id,
    )


def get_file(object_id: str, version_id: Optional[str] = None) -> bytes:
    """
    Get the file content of the specified object ID (filename) as bytes.

    This function wraps the core download logic by downloading the file from MinIO
    to a temporary path, reading its bytes, and then deleting the temporary file.

    Parameters:
    - object_id (str): The object ID (filename) to download.
    - version_id (Optional[str]): The version ID of the file to retrieve. If None,
                                  retrieves the latest version.

    Returns:
    - bytes: The file content as bytes.
    """
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_path = temp_file.name

    try:
        core_download_file(
            client=client,
            bucket_name=settings.MINIO_BUCKET_NAME,
            object_name=object_id,
            save_path=temp_path,
            version_id=version_id,
        )
        with open(temp_path, "rb") as f:
            content = f.read()
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return content
