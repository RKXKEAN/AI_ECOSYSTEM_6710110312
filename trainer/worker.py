import os
import shutil
import logging
from arq.connections import RedisSettings
from arq.worker import func
from dotenv import load_dotenv
from opentelemetry.trace import Status, StatusCode
from tracing import get_tracer

from db import update_job_status, update_inference_job_status
from train import (
    setup_logger,
    download_dataset_from_minio,
    train_ner_model,
    upload_model_to_minio,
)
from inference import predict_ner

load_dotenv()

tracer = get_tracer("trainer-worker")


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
    with tracer.start_as_current_span("train_token_classification_task") as span:
        span.set_attribute("job_id", str(job_id))
        span.set_attribute("job_db_id", job_db_id)
        logger.info(f"=== Starting Training Job: {job_id} (DB ID: {job_db_id}) ===")

        # 1. Update status to 'running'
        try:
            update_job_status(job_id, "running")
            logger.info(f"Status updated to 'running' for job {job_id}")
        except Exception as e:
            logger.error(f"Failed to update database status to 'running': {e}")

        hyperparameters = hyperparameters or {}
        dataset_name = hyperparameters.get("dataset_name", "conll2003")
        span.set_attribute("dataset_name", dataset_name)
        dataset_dir = None

        try:
            # 2. Download Dataset from MinIO
            logger.info(f"Downloading dataset '{dataset_name}' from MinIO...")
            dataset_dir = download_dataset_from_minio(dataset_name)
            logger.info(f"Dataset successfully downloaded and extracted at '{dataset_dir}'")

            # 3. Train Model
            logger.info(f"Fine-tuning NER model with hyperparameters: {hyperparameters}")
            saved_model_dir, mlflow_run_id = train_ner_model(
                dataset_path=dataset_dir,
                hyperparameters=hyperparameters,
                logger=logger,
                job_id=job_id,
                dataset_name=dataset_name,
            )
            span.set_attribute("mlflow_run_id", str(mlflow_run_id))
            logger.info(f"Training completed. Model saved at '{saved_model_dir}', MLflow Run ID: '{mlflow_run_id}'")

            # 4. Upload Model and Log to MinIO
            logger.info("Uploading trained model artifacts and log to MinIO...")
            model_object_name = upload_model_to_minio(
                model_dir=saved_model_dir,
                job_id=job_id,
                dataset_name=dataset_name
            )
            span.set_attribute("model_object", str(model_object_name))
            logger.info(f"Model successfully uploaded to MinIO: '{model_object_name}'")

            # 5. Update status to 'complete'
            update_job_status(job_id, "complete", mlflow_run_id=mlflow_run_id)
            logger.info(f"=== Job {job_id} successfully finished and status updated to 'complete' (MLflow Run ID: {mlflow_run_id}) ===")

            return {
                "job_id": job_id,
                "status": "complete",
                "model_object": model_object_name,
                "mlflow_run_id": mlflow_run_id,
            }

        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
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


async def run_inference_task(
    ctx: dict,
    job_db_id: int,
    input_text: str,
    model_version: str | None = None,
    **kwargs
) -> dict:
    """
    ARQ Background Worker task for Token Classification (NER) inference.
    Loads registered model from MLflow and performs predictions on GPU/CPU.
    """
    job_id = ctx.get("job_id") or str(job_db_id)
    logger = setup_logger(job_id)
    with tracer.start_as_current_span("run_inference_task") as span:
        span.set_attribute("job_id", str(job_id))
        span.set_attribute("job_db_id", job_db_id)
        span.set_attribute("model_version", str(model_version or ""))
        logger.info(f"=== Starting Inference Job: {job_id} (DB ID: {job_db_id}) ===")

        # 1. Update status to 'running'
        try:
            update_inference_job_status(job_id, "running")
            logger.info(f"Status updated to 'running' for inference job {job_id}")
        except Exception as e:
            logger.error(f"Failed to update database status to 'running': {e}")

        try:
            # 2. Run Inference
            logger.info(f"Running NER inference for input_text (len={len(input_text)}), model_version={model_version}")
            predictions, resolved_version = predict_ner(
                input_text=input_text,
                model_version=model_version,
                model_name="ner-conll2003"
            )
            span.set_attribute("resolved_version", resolved_version)
            span.set_attribute("predictions_count", len(predictions))
            logger.info(f"Inference completed using model version '{resolved_version}'. Extracted {len(predictions)} token entities.")

            # 3. Update status to 'complete' and save result
            update_inference_job_status(job_id, "complete", result=predictions)
            logger.info(f"=== Inference Job {job_id} finished successfully (status=complete) ===")

            return {
                "job_id": job_id,
                "status": "complete",
                "model_version": resolved_version,
                "result": predictions,
            }

        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            logger.exception(f"Inference job {job_id} failed with error: {e}")
            try:
                update_inference_job_status(job_id, "failed", result={"error": str(e)})
                logger.info(f"Status updated to 'failed' for inference job {job_id}")
            except Exception as db_err:
                logger.error(f"Failed to update database status to 'failed': {db_err}")
            raise e


class WorkerSettings:
    functions = [
        train_token_classification_task,
        func(run_inference_task, name="run_inference_task", timeout=120)
    ]
    redis_settings = RedisSettings(
        host=os.getenv("REDIS_HOST", "redis"),
        port=int(os.getenv("REDIS_PORT", "6379"))
    )
    job_timeout = 3600

