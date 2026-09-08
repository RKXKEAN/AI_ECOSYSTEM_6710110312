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
