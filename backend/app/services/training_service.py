import uuid
from sqlalchemy.orm import Session
from arq import create_pool
from arq.connections import RedisSettings
from app.core.config import settings
from app.models.training_job import TrainingJob
from app.core.logger import get_logger

logger = get_logger(__name__)

async def enqueue_training(db: Session, hyperparameters: dict) -> TrainingJob:
    """
    Register a training job in the database, queue it in arq/redis, and update the DB with arq's job ID.
    """
    # 1. Insert a temporary record with status 'queued'
    temp_id = f"temp_{uuid.uuid4()}"
    db_job = TrainingJob(
        job_id=temp_id,
        status="queued",
        hyperparameters=hyperparameters
    )
    try:
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create database entry for training job: {str(e)}")
        raise e

    # 2. Enqueue the task via ARQ
    try:
        redis = await create_pool(
            RedisSettings(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
        )
        # Enqueue train_model_task with db_job.id and hyperparameters
        arq_job = await redis.enqueue_job("train_model_task", db_job.id, hyperparameters)
        
        # 3. Update database with the actual arq job ID
        db_job.job_id = arq_job.job_id
        db.commit()
        db.refresh(db_job)
        
        logger.info(f"Training job successfully enqueued: DB ID={db_job.id}, ARQ Job ID={arq_job.job_id}")
        return db_job
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to enqueue training job for DB ID {db_job.id}: {str(e)}")
        try:
            db_job.status = "failed"
            db.commit()
        except Exception:
            db.rollback()
        raise e

def get_job_metrics(db: Session, job_id: str) -> dict:
    """
    Retrieve real status metrics of the training job.
    Raises ValueError if job is not found.
    """
    try:
        job = db.query(TrainingJob).filter(TrainingJob.job_id == job_id).first()
        if not job:
            logger.error(f"Job not found: {job_id}")
            raise ValueError("job not found")

        # Determine progress based on status
        if job.status == "complete":
            progress = 1.0
        elif job.status == "running":
            progress = 0.5
        elif job.status == "failed":
            progress = 0.0
        else:
            progress = 0.0

        dataset_name = job.hyperparameters.get("dataset_name", "unknown") if job.hyperparameters else "unknown"

        metrics = {
            "job_id": job.job_id,
            "status": job.status,
            "progress": progress,
            "dataset_name": dataset_name
        }
        logger.info(f"Retrieved metrics for job {job_id} successfully")
        return metrics
    except ValueError as ve:
        raise ve
    except Exception as e:
        logger.error(f"Error retrieving metrics for job {job_id}: {str(e)}")
        raise e
