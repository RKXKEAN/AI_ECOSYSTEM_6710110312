import json
from pathlib import Path
from sqlalchemy.orm import Session
from app.models.feedback import Feedback
from app.core.logger import get_logger

logger = get_logger(__name__)

# Path to the application log file
LOG_FILE = Path(__file__).resolve().parent.parent.parent / "logs" / "app.log"

def submit_feedback(db: Session, prediction_id: str, is_correct: bool, comment: str | None = None) -> Feedback:
    """
    Save user feedback for a specific prediction ID to the database.
    """
    try:
        db_feedback = Feedback(
            prediction_id=prediction_id,
            is_correct=is_correct,
            comment=comment
        )
        db.add(db_feedback)
        db.commit()
        db.refresh(db_feedback)
        logger.info(f"Feedback for prediction '{prediction_id}' submitted successfully (ID: {db_feedback.id})")
        return db_feedback
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to submit feedback for prediction '{prediction_id}': {str(e)}")
        raise e

def get_drift() -> dict:
    """
    Check for model drift (Mock implementation).
    """
    try:
        data = {
            "status": "normal",
            "drift_score": 0.02,
            "message": "No significant drift detected. (Mock drift score - awaiting real data integration)"
        }
        logger.info("Retrieved model drift status successfully")
        return data
    except Exception as e:
        logger.error(f"Failed to retrieve model drift: {str(e)}")
        raise e

def get_dashboard(db: Session) -> dict:
    """
    Retrieve monitoring dashboard metrics.
    total_predictions corresponds to the total number of feedbacks in the system.
    """
    try:
        total_predictions = db.query(Feedback).count()
        data = {
            "uptime_seconds": 86400.0,  # Mocked 24 hours
            "total_predictions": total_predictions,
            "active_alerts": 0
        }
        logger.info(f"Dashboard metrics retrieved successfully (total_predictions: {total_predictions})")
        return data
    except Exception as e:
        logger.error(f"Failed to retrieve dashboard metrics: {str(e)}")
        raise e

def get_logs(limit: int = 50) -> dict:
    """
    Read latest system logs from the tail of app.log.
    Note: As per requirement, this function does NOT log its own activity to avoid infinite loops.
    """
    if not LOG_FILE.exists():
        return {"logs": [], "count": 0}
        
    log_entries = []
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        # Iterate from the end of file to get the newest logs first
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                # Map potential missing keys from schema safely
                log_entry = {
                    "timestamp": entry.get("timestamp", ""),
                    "level": entry.get("level", ""),
                    "logger": entry.get("logger", ""),
                    "message": entry.get("message", ""),
                    "module": entry.get("module", None)
                }
                log_entries.append(log_entry)
                if len(log_entries) >= limit:
                    break
            except Exception:
                # Skip invalid json formats if any
                continue
    except Exception:
        # Return empty on any reading exceptions to prevent crash
        return {"logs": [], "count": 0}
        
    return {"logs": log_entries, "count": len(log_entries)}
