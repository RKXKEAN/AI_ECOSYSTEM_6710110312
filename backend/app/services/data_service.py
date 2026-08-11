from sqlalchemy.orm import Session
from app.models.dataset import Dataset
from app.core.logger import get_logger

logger = get_logger(__name__)

def ingest_dataset(db: Session, name: str, storage_path: str) -> Dataset:
    """
    Ingest a new dataset.
    Raises ValueError if a dataset with the same name already exists.
    """
    try:
        existing = db.query(Dataset).filter(Dataset.name == name).first()
        if existing:
            logger.error(f"Ingestion failed: Dataset name '{name}' already exists")
            raise ValueError("Dataset name already exists")
            
        db_dataset = Dataset(
            name=name,
            storage_path=storage_path,
            status="pending"
        )
        db.add(db_dataset)
        db.commit()
        db.refresh(db_dataset)
        logger.info(f"Dataset '{name}' ingested successfully with status 'pending' (ID: {db_dataset.id})")
        return db_dataset
    except ValueError as ve:
        raise ve
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to ingest dataset '{name}': {str(e)}")
        raise e

def list_datasets(db: Session) -> list[Dataset]:
    """
    Retrieve all datasets from the registry.
    """
    try:
        datasets = db.query(Dataset).all()
        logger.info(f"Retrieved {len(datasets)} datasets")
        return datasets
    except Exception as e:
        logger.error(f"Failed to list datasets: {str(e)}")
        raise e
