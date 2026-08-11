from sqlalchemy.orm import Session
from app.models.model_registry import Model, ModelVersion
from app.core.logger import get_logger

logger = get_logger(__name__)

def register_model(db: Session, name: str, created_by: str, dataset_used: str) -> Model:
    """
    Register a new model in the registry and automatically seed a default version 'v1' for testing.
    """
    try:
        db_model = Model(
            name=name,
            created_by=created_by,
            dataset_used=dataset_used
        )
        db.add(db_model)
        db.commit()
        db.refresh(db_model)
        
        # Create a default model version (v1) to make the model testable
        default_version = ModelVersion(
            model_id=db_model.id,
            version="v1",
            metrics={"accuracy": 0.0, "loss": 0.0},
            storage_path=f"models/{name}/v1/weights.bin",
            is_deployed=False
        )
        db.add(default_version)
        db.commit()
        db.refresh(db_model)
        
        logger.info(f"Model '{name}' registered successfully with ID {db_model.id} and default version v1")
        return db_model
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to register model '{name}': {str(e)}")
        raise e

def get_versions(db: Session, model_id: int) -> list[ModelVersion]:
    """
    Retrieve all versions for a given model ID.
    Raises ValueError if the model itself does not exist.
    """
    try:
        model = db.query(Model).filter(Model.id == model_id).first()
        if not model:
            logger.error(f"Failed to get versions: Model ID {model_id} not found")
            raise ValueError("Model not found")
            
        versions = db.query(ModelVersion).filter(ModelVersion.model_id == model_id).all()
        logger.info(f"Retrieved {len(versions)} versions for Model ID {model_id}")
        return versions
    except ValueError as ve:
        raise ve
    except Exception as e:
        logger.error(f"Error retrieving versions for Model ID {model_id}: {str(e)}")
        raise e

def update_metrics(db: Session, model_id: int, version_id: int, metrics: dict) -> ModelVersion:
    """
    Update the evaluation metrics of a specific model version.
    Raises ValueError if either the model or the model version is not found.
    """
    try:
        model = db.query(Model).filter(Model.id == model_id).first()
        if not model:
            logger.error(f"Failed to update metrics: Model ID {model_id} not found")
            raise ValueError("Model not found")
            
        version = db.query(ModelVersion).filter(
            ModelVersion.id == version_id,
            ModelVersion.model_id == model_id
        ).first()
        if not version:
            logger.error(f"Failed to update metrics: Version ID {version_id} not found for Model ID {model_id}")
            raise ValueError("Model version not found")
            
        version.metrics = metrics
        db.commit()
        db.refresh(version)
        logger.info(f"Metrics updated successfully for Model ID {model_id}, Version ID {version_id}")
        return version
    except ValueError as ve:
        raise ve
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update metrics for Model ID {model_id}, Version ID {version_id}: {str(e)}")
        raise e

def deploy_model(db: Session, model_id: int, version_id: int) -> ModelVersion:
    """
    Deploy a specific model version (mock deployment - sets is_deployed to True).
    Raises ValueError if either the model or the model version is not found.
    """
    try:
        model = db.query(Model).filter(Model.id == model_id).first()
        if not model:
            logger.error(f"Failed to deploy model: Model ID {model_id} not found")
            raise ValueError("Model not found")
            
        version = db.query(ModelVersion).filter(
            ModelVersion.id == version_id,
            ModelVersion.model_id == model_id
        ).first()
        if not version:
            logger.error(f"Failed to deploy: Version ID {version_id} not found for Model ID {model_id}")
            raise ValueError("Model version not found")
            
        version.is_deployed = True
        db.commit()
        db.refresh(version)
        logger.info(f"Model ID {model_id}, Version ID {version_id} deployed successfully")
        return version
    except ValueError as ve:
        raise ve
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to deploy Model ID {model_id}, Version ID {version_id}: {str(e)}")
        raise e
