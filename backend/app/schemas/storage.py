from pydantic import BaseModel
from typing import List

class UploadResponse(BaseModel):
    object_name: str
    version_id: str

class VersionsResponse(BaseModel):
    object_name: str
    versions: List[str]
