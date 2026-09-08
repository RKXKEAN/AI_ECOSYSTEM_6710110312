import uuid
from typing import Optional
from sqlalchemy.orm import Session
from arq import create_pool
from arq.connections import RedisSettings

from app.core.config import settings
from app.core.logger import get_logger
from app.models.inference_job import InferenceJob
from app.schemas.inference import ModelInfo

logger = get_logger(__name__)

# Legacy Mock Models (retained for backward compatibility with /models endpoint)
MOCK_MODELS = [
    {"name": "ner-conll2003", "version": "1.0", "status": "ready"},
    {"name": "default", "version": "1.0", "status": "ready"},
    {"name": "sentiment-analyzer", "version": "0.9", "status": "ready"}
]


def list_models() -> list[ModelInfo]:
    """
    คืนรายชื่อ model ทั้งหมด
    """
    return [ModelInfo(**m) for m in MOCK_MODELS]


async def enqueue_inference(
    db: Session,
    text: str,
    model_version: Optional[str] = None
) -> InferenceJob:
    """
    Register an inference job in the database, queue it in arq/redis,
    and update the DB with arq's job ID.
    """
    temp_id = f"temp_{uuid.uuid4()}"
    db_job = InferenceJob(
        job_id=temp_id,
        status="queued",
        input_text=text,
        model_version=model_version
    )
    try:
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create database entry for inference job: {str(e)}")
        raise e

    try:
        redis = await create_pool(
            RedisSettings(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
        )
        arq_job = await redis.enqueue_job(
            "run_inference_task",
            db_job.id,
            text,
            model_version
        )
        db_job.job_id = arq_job.job_id
        db.commit()
        db.refresh(db_job)

        logger.info(
            f"Inference job successfully enqueued: DB ID={db_job.id}, "
            f"ARQ Job ID={arq_job.job_id}, Model Version={model_version}"
        )
        return db_job
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to enqueue inference job for DB ID {db_job.id}: {str(e)}")
        try:
            db_job.status = "failed"
            db.commit()
        except Exception:
            db.rollback()
        raise e


def get_inference_result(db: Session, job_id: str) -> InferenceJob:
    """
    Retrieve real status and result of the inference job.
    Raises ValueError if job is not found.
    """
    try:
        job = db.query(InferenceJob).filter(InferenceJob.job_id == job_id).first()
        if not job:
            logger.error(f"Inference job not found: {job_id}")
            raise ValueError("job not found")

        logger.info(f"Retrieved result for inference job {job_id} successfully (status={job.status})")
        return job
    except ValueError as ve:
        raise ve
    except Exception as e:
        logger.error(f"Error retrieving inference job {job_id}: {str(e)}")
        raise e
