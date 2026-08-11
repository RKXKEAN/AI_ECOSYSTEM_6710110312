from fastapi import APIRouter, HTTPException
from app.schemas.training import TrainingJobRequest, TrainingJobResponse, TrainingJobStatus
from app.services.training_service import create_job, get_job_status

router = APIRouter(prefix="/training", tags=["Training"])

@router.post("/jobs", response_model=TrainingJobResponse)
def post_create_job(request: TrainingJobRequest):
    """
    สร้าง Training Job ใหม่
    """
    job_id = create_job(request.dataset_name, request.epochs, request.model_name)
    return TrainingJobResponse(job_id=job_id, status="queued")

@router.get("/jobs/{job_id}", response_model=TrainingJobStatus)
def get_job(job_id: str):
    """
    ดึงสถานะความคืบหน้าของ Training Job
    """
    job = get_job_status(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return TrainingJobStatus(**job)
