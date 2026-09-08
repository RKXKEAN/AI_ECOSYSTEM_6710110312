from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logger import get_logger
from app.schemas.inference import (
    ModelInfo,
    PredictRequest,
    PredictResponse,
    InferenceResultResponse,
)
from app.services.inference_service import (
    list_models,
    enqueue_inference,
    get_inference_result,
)

router = APIRouter(prefix="/inference", tags=["Inference"])
logger = get_logger(__name__)


@router.get("/models", response_model=list[ModelInfo])
def get_models():
    """
    ดึงรายชื่อ model ทั้งหมด
    """
    return list_models()


@router.post("/predict", response_model=PredictResponse)
async def post_predict(request: PredictRequest, db: Session = Depends(get_db)):
    """
    สร้าง Inference Job ใหม่ สำหรับ Token Classification (NER)
    ประมวลผลผ่าน GPU Worker (trainer-worker) ด้วย MLflow Model Registry
    """
    try:
        input_text = request.text or request.input_text or ""
        job = await enqueue_inference(
            db=db,
            text=input_text,
            model_version=request.model_version
        )
        logger.info(f"API: Enqueued inference job {job.job_id} successfully")
        return PredictResponse(
            job_id=job.job_id,
            status=job.status
        )
    except Exception as e:
        logger.error(f"API: Failed to enqueue inference job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/jobs/{job_id}", response_model=InferenceResultResponse)
def get_job(job_id: str, db: Session = Depends(get_db)):
    """
    ดึงผลการทำนายหรือสถานะของ Inference Job ตาม job_id
    """
    try:
        job = get_inference_result(db, job_id)
        return InferenceResultResponse.model_validate(job)
    except ValueError as e:
        logger.error(f"API: Inference job {job_id} not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="job not found"
        )
    except Exception as e:
        logger.error(f"API: Error retrieving inference job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
