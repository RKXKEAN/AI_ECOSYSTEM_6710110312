from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.logger import get_logger
from app.schemas.training import TrainingJobRequest, TrainingJobResponse, TrainingJobStatus
from app.services.training_service import enqueue_training, get_job_metrics

router = APIRouter(prefix="/training", tags=["Training"])
logger = get_logger(__name__)

@router.post("/jobs", response_model=TrainingJobResponse)
async def post_create_job(request: TrainingJobRequest, db: Session = Depends(get_db)):
    """
    สร้าง Training Job ใหม่
    """
    try:
        hyperparameters = {
            "dataset_name": request.dataset_name,
            "epochs": request.epochs,
            "model_name": request.model_name
        }
        job = await enqueue_training(db, hyperparameters)
        logger.info(f"API: Enqueued job {job.job_id} successfully")
        return TrainingJobResponse(job_id=job.job_id, status=job.status)
    except Exception as e:
        logger.error(f"API: Failed to enqueue training job: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/jobs/{job_id}", response_model=TrainingJobStatus)
def get_job(job_id: str, db: Session = Depends(get_db)):
    """
    ดึงสถานะความคืบหน้าของ Training Job
    """
    try:
        metrics = get_job_metrics(db, job_id)
        return TrainingJobStatus(**metrics)
    except ValueError as e:
        logger.error(f"API: Job {job_id} not found: {str(e)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job not found")
    except Exception as e:
        logger.error(f"API: Error retrieving status for job {job_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/jobs/{job_id}/metrics", response_model=TrainingJobStatus)
def get_job_metrics_endpoint(job_id: str, db: Session = Depends(get_db)):
    """
    ดึงสถานะความคืบหน้าของ Training Job
    """
    try:
        metrics = get_job_metrics(db, job_id)
        return TrainingJobStatus(**metrics)
    except ValueError as e:
        logger.error(f"API: Job {job_id} not found: {str(e)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job not found")
    except Exception as e:
        logger.error(f"API: Error retrieving status for job {job_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
