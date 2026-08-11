import asyncio
from sqlalchemy.sql import func
from arq.connections import RedisSettings
from app.core.database import SessionLocal
from app.models.training_job import TrainingJob
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

async def train_model_task(ctx, job_db_id: int, hyperparameters: dict):
    logger.info(f"Worker: Starting training task for job DB ID: {job_db_id}")
    
    # 1. Update status to 'running'
    db = SessionLocal()
    try:
        job = db.query(TrainingJob).filter(TrainingJob.id == job_db_id).first()
        if not job:
            logger.error(f"Worker: Job with DB ID {job_db_id} not found in database")
            return
        
        job.status = "running"
        job.updated_at = func.now()
        db.commit()
        logger.info(f"Worker: Job DB ID {job_db_id} status updated to 'running'")
    except Exception as e:
        db.rollback()
        logger.error(f"Worker: Failed to update status to 'running' for job {job_db_id}: {str(e)}")
        db.close()
        return
        
    # 2. Simulate training
    try:
        await asyncio.sleep(10)
        
        # 3. Update status to 'complete'
        job = db.query(TrainingJob).filter(TrainingJob.id == job_db_id).first()
        if job:
            job.status = "complete"
            job.updated_at = func.now()
            db.commit()
            logger.info(f"Worker: Job DB ID {job_db_id} status updated to 'complete' successfully")
    except Exception as e:
        db.rollback()
        logger.error(f"Worker: Error during training simulation for job {job_db_id}: {str(e)}")
        try:
            job = db.query(TrainingJob).filter(TrainingJob.id == job_db_id).first()
            if job:
                job.status = "failed"
                job.updated_at = func.now()
                db.commit()
                logger.info(f"Worker: Job DB ID {job_db_id} status marked as 'failed'")
        except Exception as db_err:
            db.rollback()
            logger.error(f"Worker: Failed to mark job {job_db_id} as 'failed' in DB: {str(db_err)}")
    finally:
        db.close()

class WorkerSettings:
    functions = [train_model_task]
    redis_settings = RedisSettings(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT
    )
