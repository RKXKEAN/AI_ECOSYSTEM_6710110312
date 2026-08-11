from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class FeedbackRequest(BaseModel):
    prediction_id: str
    is_correct: bool
    comment: Optional[str] = None

class FeedbackResponse(BaseModel):
    id: int
    prediction_id: str
    is_correct: bool
    comment: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}

class DriftResponse(BaseModel):
    status: str
    drift_score: float
    message: str

    model_config = {"from_attributes": True}

class DashboardResponse(BaseModel):
    uptime_seconds: float
    total_predictions: int
    active_alerts: int

    model_config = {"from_attributes": True}

class LogEntry(BaseModel):
    timestamp: str
    level: str
    logger: str
    message: str
    module: Optional[str] = None

    model_config = {"from_attributes": True}

class LogsResponse(BaseModel):
    logs: List[LogEntry]
    count: int

    model_config = {"from_attributes": True}
