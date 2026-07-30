from pydantic import BaseModel

class TrainingJobRequest(BaseModel):
    dataset_name: str
    epochs: int = 10
    model_name: str = "default"

class TrainingJobResponse(BaseModel):
    job_id: str
    status: str

class TrainingJobStatus(BaseModel):
    job_id: str
    status: str
    progress: float
    dataset_name: str
