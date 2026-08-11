from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class IngestRequest(BaseModel):
    name: str
    storage_path: str

class IngestResponse(BaseModel):
    id: int
    name: str
    storage_path: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}

class DatasetInfo(BaseModel):
    id: int
    name: str
    storage_path: str
    status: str
    row_count: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}

class DatasetListResponse(BaseModel):
    datasets: List[DatasetInfo]

    model_config = {"from_attributes": True}
