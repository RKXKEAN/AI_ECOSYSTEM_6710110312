from pydantic import BaseModel
from typing import List, Literal, Optional

class UploadResponse(BaseModel):
    object_name: str
    version_id: str

class VersionsResponse(BaseModel):
    object_name: str
    versions: List[str]

class CreateBucketRequest(BaseModel):
    bucket_name: str

class CreateBucketResponse(BaseModel):
    bucket_name: str
    created: bool

class PresignedUrlRequest(BaseModel):
    object_name: str
    method: Literal["upload", "download"]
    expires_minutes: int = 60

class PresignedUrlResponse(BaseModel):
    url: str
    expires_minutes: int

class ObjectInfo(BaseModel):
    object_name: str
    size: int
    last_modified: Optional[str] = None

class ObjectListResponse(BaseModel):
    objects: List[ObjectInfo]
