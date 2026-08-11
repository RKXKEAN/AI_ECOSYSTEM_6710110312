import io
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import StreamingResponse

from app.services.storage_service import upload_file, list_versions, get_file, create_bucket, generate_presigned_url, list_objects
from app.schemas.storage import (
    UploadResponse, 
    VersionsResponse, 
    CreateBucketRequest, 
    CreateBucketResponse, 
    PresignedUrlRequest, 
    PresignedUrlResponse,
    ObjectListResponse,
    ObjectInfo
)

router = APIRouter(prefix="/storage", tags=["Storage"])

@router.post("/upload", response_model=UploadResponse)
async def upload_storage_file(file: UploadFile = File(...)):
    filename = file.filename or "file"
    try:
        file_bytes = await file.read()
        object_name = upload_file(file_bytes=file_bytes, filename=filename)
        versions = list_versions(object_id=object_name)
        version_id = versions[0] if versions else "unknown"
        return UploadResponse(object_name=object_name, version_id=version_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/objects", response_model=ObjectListResponse)
def get_objects():
    try:
        objects = list_objects()
        object_list = [ObjectInfo(**o) for o in objects]
        return ObjectListResponse(objects=object_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list objects: {str(e)}")

@router.get("/{object_name}/versions", response_model=VersionsResponse)
def get_file_versions(object_name: str):
    try:
        versions = list_versions(object_id=object_name)
        return VersionsResponse(object_name=object_name, versions=versions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list versions: {str(e)}")

@router.get("/{object_name}")
def download_storage_file(object_name: str, version_id: str | None = None):
    try:
        content = get_file(object_id=object_name, version_id=version_id)
        return StreamingResponse(
            io.BytesIO(content),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={object_name}"}
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"File not found or failed to retrieve: {str(e)}")

@router.post("/buckets", response_model=CreateBucketResponse, status_code=status.HTTP_201_CREATED)
def create_storage_bucket(request: CreateBucketRequest):
    try:
        create_bucket(request.bucket_name)
        return CreateBucketResponse(bucket_name=request.bucket_name, created=True)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create bucket: {str(e)}")

@router.post("/presigned-url", response_model=PresignedUrlResponse)
def get_presigned_url(request: PresignedUrlRequest):
    try:
        url = generate_presigned_url(
            object_name=request.object_name,
            method=request.method,
            expires_minutes=request.expires_minutes
        )
        return PresignedUrlResponse(url=url, expires_minutes=request.expires_minutes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate presigned URL: {str(e)}")
