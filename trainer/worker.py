import os
import shutil
import logging
from arq.connections import RedisSettings
from dotenv import load_dotenv

from db import update_job_status
from train import (
    setup_logger,
    download_dataset_from_minio,
    train_ner_model,
    upload_model_to_minio,
)

load_dotenv()


async def train_token_classification_task(
    ctx: dict,
    job_db_id: int,
    hyperparameters: dict | None = None,
    **kwargs
) -> dict:
    """
    ARQ Background Worker task for Token Classification (NER) fine-tuning.
    """
    job_id = ctx.get("job_id") or str(job_db_id)
    logger = setup_logger(job_id)
    logger.info(f"=== Starting Training Job: {job_id} (DB ID: {job_db_id}) ===")

    # 1. Update status to 'running'
    try:
        update_job_status(job_id, "running")
        logger.info(f"Status updated to 'running' for job {job_id}")
    except Exception as e:
        logger.error(f"Failed to update database status to 'running': {e}")

    hyperparameters = hyperparameters or {}
    dataset_name = hyperparameters.get("dataset_name", "conll2003")
    dataset_dir = None

    try:
        # 2. Download Dataset from MinIO
        logger.info(f"Downloading dataset '{dataset_name}' from MinIO...")
        dataset_dir = download_dataset_from_minio(dataset_name)
        logger.info(f"Dataset successfully downloaded and extracted at '{dataset_dir}'")

        # 3. Train Model
        logger.info(f"Fine-tuning NER model with hyperparameters: {hyperparameters}")
        saved_model_dir = train_ner_model(
            dataset_path=dataset_dir,
            hyperparameters=hyperparameters,
            logger=logger
        )
        logger.info(f"Training completed. Model saved at '{saved_model_dir}'")

        # 4. Upload Model and Log to MinIO
        logger.info("Uploading trained model artifacts and log to MinIO...")
        model_object_name = upload_model_to_minio(
            model_dir=saved_model_dir,
            job_id=job_id,
            dataset_name=dataset_name
        )
        logger.info(f"Model successfully uploaded to MinIO: '{model_object_name}'")

        # 5. Update status to 'complete'
        update_job_status(job_id, "complete")
        logger.info(f"=== Job {job_id} successfully finished and status updated to 'complete' ===")

        return {
            "job_id": job_id,
            "status": "complete",
            "model_object": model_object_name,
        }

    except Exception as e:
        logger.exception(f"Training job {job_id} failed with error: {e}")
        try:
            update_job_status(job_id, "failed")
            logger.info(f"Status updated to 'failed' for job {job_id}")
        except Exception as db_err:
            logger.error(f"Failed to update database status to 'failed': {db_err}")
        raise e
    finally:
        # Cleanup temporary extracted dataset directory
        if dataset_dir and os.path.exists(dataset_dir):
            try:
                shutil.rmtree(dataset_dir, ignore_errors=True)
                logger.info(f"Cleaned up temporary dataset directory '{dataset_dir}'")
            except Exception as clean_err:
                logger.warning(f"Could not clean up temporary dataset dir: {clean_err}")


class WorkerSettings:
    functions = [train_token_classification_task]
    redis_settings = RedisSettings(
        host=os.getenv("REDIS_HOST", "redis"),
        port=int(os.getenv("REDIS_PORT", "6379"))
    )
    job_timeout = 3600
