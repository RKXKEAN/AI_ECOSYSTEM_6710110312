from datetime import datetime
from pydantic import BaseModel

class TrainingJobRequest(BaseModel):
    dataset_name: str
    epochs: int = 10
    model_name: str = "default"
    scheduled_at: datetime | None = None

class TrainingJobResponse(BaseModel):
    job_id: str
    status: str
    scheduled_at: datetime | None = None
    mlflow_run_id: str | None = None

class TrainingJobStatus(BaseModel):
    job_id: str
    status: str
    progress: float
    dataset_name: str
    mlflow_run_id: str | None = None
