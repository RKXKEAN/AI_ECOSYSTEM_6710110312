from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.logger import get_logger
from app.schemas.data import IngestRequest, IngestResponse, DatasetListResponse
from app.services.data_service import ingest_dataset, list_datasets

router = APIRouter(prefix="/api/v1/data", tags=["Data Management"])
logger = get_logger(__name__)

@router.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
def ingest(request: IngestRequest, db: Session = Depends(get_db)):
    """
    Ingest a new dataset by registering its name and storage path.
    """
    try:
        dataset = ingest_dataset(db, request.name, request.storage_path)
        logger.info(f"API: Ingested dataset '{request.name}' successfully")
        return dataset
    except ValueError as e:
        logger.error(f"API: Ingestion failed for dataset '{request.name}': {str(e)}")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f"API: Unexpected error ingesting dataset '{request.name}': {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/datasets", response_model=DatasetListResponse)
def get_datasets(db: Session = Depends(get_db)):
    """
    Retrieve list of all datasets.
    """
    try:
        datasets = list_datasets(db)
        return DatasetListResponse(datasets=datasets)
    except Exception as e:
        logger.error(f"API: Failed to retrieve datasets: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
