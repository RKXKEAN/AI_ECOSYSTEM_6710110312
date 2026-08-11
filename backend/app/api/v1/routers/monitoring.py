from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.logger import get_logger
from app.schemas.monitoring import (
    FeedbackRequest,
    FeedbackResponse,
    DriftResponse,
    DashboardResponse,
    LogsResponse,
)
from app.services.monitoring_service import (
    submit_feedback,
    get_drift,
    get_dashboard,
    get_logs,
)

router = APIRouter(prefix="/api/v1/monitoring", tags=["Monitoring"])
logger = get_logger(__name__)

@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def post_feedback(request: FeedbackRequest, db: Session = Depends(get_db)):
    """
    Submit user feedback on a specific prediction.
    """
    try:
        feedback = submit_feedback(db, request.prediction_id, request.is_correct, request.comment)
        logger.info(f"API: Submitted feedback for prediction '{request.prediction_id}' successfully")
        return feedback
    except Exception as e:
        logger.error(f"API: Failed to submit feedback for prediction '{request.prediction_id}': {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/drift", response_model=DriftResponse)
def get_drift_status():
    """
    Retrieve model drift status.
    """
    try:
        return get_drift()
    except Exception as e:
        logger.error(f"API: Failed to get drift status: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard_metrics(db: Session = Depends(get_db)):
    """
    Retrieve system dashboard metrics.
    """
    try:
        return get_dashboard(db)
    except Exception as e:
        logger.error(f"API: Failed to get dashboard metrics: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/logs", response_model=LogsResponse)
def get_system_logs(limit: int = 50):
    """
    Retrieve system logs from app.log (most recent entries first).
    """
    try:
        return get_logs(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
