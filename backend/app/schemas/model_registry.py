from pydantic import BaseModel
from datetime import datetime
from typing import Dict, List, Any

class ModelRegisterRequest(BaseModel):
    name: str
    created_by: str
    dataset_used: str

class ModelRegisterResponse(BaseModel):
    id: int
    name: str
    created_by: str
    dataset_used: str
    created_at: datetime

    model_config = {"from_attributes": True}

class ModelVersionInfo(BaseModel):
    id: int
    version: str
    metrics: Dict[str, Any]
    storage_path: str
    is_deployed: bool
    created_at: datetime

    model_config = {"from_attributes": True}

class ModelVersionListResponse(BaseModel):
    model_id: int
    versions: List[ModelVersionInfo]

    model_config = {"from_attributes": True}

class UpdateMetricsRequest(BaseModel):
    metrics: Dict[str, Any]

class DeployResponse(BaseModel):
    model_id: int
    version_id: int
    deployed: bool
    message: str

    model_config = {"from_attributes": True}
