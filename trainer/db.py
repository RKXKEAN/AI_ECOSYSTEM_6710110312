import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://admin:password123@postgres:5432/ai_backend"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)


def update_job_status(
    job_id: str,
    status: str,
    mlflow_run_id: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None
) -> None:
    """
    Update the status and updated_at timestamp of a training job in PostgreSQL.
    Optionally updates mlflow_run_id if provided.
    Uses raw SQL query via SQLAlchemy text() to avoid duplicate ORM models.
    """
    try:
        if mlflow_run_id:
            query = text("""
                UPDATE training_jobs
                SET status = :status, mlflow_run_id = :mlflow_run_id, updated_at = :updated_at
                WHERE job_id = :job_id
            """)
            params = {
                "status": status,
                "mlflow_run_id": mlflow_run_id,
                "updated_at": datetime.utcnow(),
                "job_id": job_id
            }
        else:
            query = text("""
                UPDATE training_jobs
                SET status = :status, updated_at = :updated_at
                WHERE job_id = :job_id
            """)
            params = {
                "status": status,
                "updated_at": datetime.utcnow(),
                "job_id": job_id
            }
        with engine.begin() as conn:
            result = conn.execute(query, params)
            logger.info(f"Database: Updated job '{job_id}' status to '{status}' (mlflow_run_id: {mlflow_run_id}, rows affected: {result.rowcount})")
    except Exception as e:
        logger.error(f"Database error updating job '{job_id}' status: {e}")
        raise e


def update_inference_job_status(
    job_id: str,
    status: str,
    result: Optional[Any] = None
) -> None:
    """
    Update the status, result, and updated_at timestamp of an inference job in PostgreSQL.
    Uses raw SQL query via SQLAlchemy text() to avoid duplicate ORM models.
    """
    import json
    try:
        result_json = json.dumps(result) if result is not None else None
        if result_json is not None:
            query = text("""
                UPDATE inference_jobs
                SET status = :status, result = :result, updated_at = :updated_at
                WHERE job_id = :job_id
            """)
            params = {
                "status": status,
                "result": result_json,
                "updated_at": datetime.utcnow(),
                "job_id": job_id
            }
        else:
            query = text("""
                UPDATE inference_jobs
                SET status = :status, updated_at = :updated_at
                WHERE job_id = :job_id
            """)
            params = {
                "status": status,
                "updated_at": datetime.utcnow(),
                "job_id": job_id
            }
        with engine.begin() as conn:
            exec_res = conn.execute(query, params)
            if exec_res.rowcount == 0 and job_id.isdigit():
                # Fallback to update by primary key id if job_id was numeric ID
                if result_json is not None:
                    fb_query = text("""
                        UPDATE inference_jobs
                        SET status = :status, result = :result, updated_at = :updated_at
                        WHERE id = :id
                    """)
                else:
                    fb_query = text("""
                        UPDATE inference_jobs
                        SET status = :status, updated_at = :updated_at
                        WHERE id = :id
                    """)
                exec_res = conn.execute(fb_query, {**params, "id": int(job_id)})
            logger.info(f"Database: Updated inference job '{job_id}' status to '{status}' (rows affected: {exec_res.rowcount})")
    except Exception as e:
        logger.error(f"Database error updating inference job '{job_id}' status: {e}")
        raise e

