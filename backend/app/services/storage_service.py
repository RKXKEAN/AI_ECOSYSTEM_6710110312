import os
import tempfile
from typing import Optional
from datetime import timedelta

from app.core.config import settings
from app.core.logger import get_logger
from app.core.minio_versioning import (
    get_client,
    enable_versioning,
    upload_file as core_upload_file,
    list_versions as core_list_versions,
    download_file as core_download_file,
)

# Initialize logger
logger = get_logger(__name__)

# Initialize MinIO Client
client = get_client()

# Auto-initialize bucket and versioning configuration on startup
try:
    if not client.bucket_exists(settings.MINIO_BUCKET_NAME):
        client.make_bucket(settings.MINIO_BUCKET_NAME)
    enable_versioning(client, settings.MINIO_BUCKET_NAME)
except Exception as e:
    logger.error(f"Failed to auto-initialize MinIO bucket or versioning: {e}")


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


def list_objects() -> list:
    """
    List all objects in the default MinIO bucket.
    """
    try:
        bucket_name = settings.MINIO_BUCKET_NAME
        objects = client.list_objects(bucket_name)
        
        result = []
        for o in objects:
            result.append({
                "object_name": o.object_name,
                "size": o.size,
                "last_modified": o.last_modified.isoformat() if o.last_modified else None
            })
            
        logger.info(f"Successfully listed {len(result)} objects in bucket '{bucket_name}'")
        return result
    except Exception as e:
        logger.error(f"Failed to list objects in bucket: {str(e)}")
        raise e


def create_bucket(bucket_name: str) -> bool:
    """
    Create a new MinIO bucket.
    Raises ValueError if the bucket already exists.
    """
    try:
        if client.bucket_exists(bucket_name):
            logger.error(f"Failed to create bucket: '{bucket_name}' already exists")
            raise ValueError(f"Bucket '{bucket_name}' already exists")
        
        client.make_bucket(bucket_name)
        logger.info(f"Bucket '{bucket_name}' created successfully")
        return True
    except ValueError as ve:
        raise ve
    except Exception as e:
        logger.error(f"Failed to create bucket '{bucket_name}': {str(e)}")
        raise e


def generate_presigned_url(object_name: str, method: str, expires_minutes: int = 60) -> str:
    """
    Generate a presigned URL for upload (PUT) or download (GET) for an object in MinIO.
    """
    try:
        bucket_name = settings.MINIO_BUCKET_NAME
        expires = timedelta(minutes=expires_minutes)
        
        if method == "upload":
            url = client.presigned_put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                expires=expires
            )
        elif method == "download":
            url = client.presigned_get_object(
                bucket_name=bucket_name,
                object_name=object_name,
                expires=expires
            )
        else:
            raise ValueError(f"Invalid method: {method}")
            
        logger.info(f"Generated presigned {method} URL for '{object_name}' in bucket '{bucket_name}' (expires: {expires_minutes}m)")
        return url
    except Exception as e:
        logger.error(f"Failed to generate presigned {method} URL for '{object_name}': {str(e)}")
        raise e
