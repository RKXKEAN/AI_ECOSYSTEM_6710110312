from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.logger import get_logger
from app.schemas.model_registry import (
    ModelRegisterRequest,
    ModelRegisterResponse,
    ModelVersionInfo,
    ModelVersionListResponse,
    UpdateMetricsRequest,
    DeployResponse,
)
from app.services.model_registry_service import (
    register_model,
    get_versions,
    update_metrics,
    deploy_model,
)

router = APIRouter(prefix="/api/v1/models", tags=["Model Registry"])
logger = get_logger(__name__)

@router.post("/register", response_model=ModelRegisterResponse, status_code=status.HTTP_201_CREATED)
def register(request: ModelRegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new model in the registry (automatically creates version v1).
    """
    try:
        model = register_model(db, request.name, request.created_by, request.dataset_used)
        logger.info(f"API: Registered model '{request.name}' successfully")
        return model
    except Exception as e:
        logger.error(f"API: Failed to register model '{request.name}': {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{model_id}/versions", response_model=ModelVersionListResponse)
def get_model_versions(model_id: int, db: Session = Depends(get_db)):
    """
    Retrieve all versions of the specified model.
    """
    try:
        versions = get_versions(db, model_id)
        return ModelVersionListResponse(model_id=model_id, versions=versions)
    except ValueError as e:
        logger.error(f"API: Model ID {model_id} not found: {str(e)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"API: Failed to get versions for Model ID {model_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/{id}/metrics", response_model=ModelVersionInfo)
def update_model_metrics(id: int, version_id: int, request: UpdateMetricsRequest, db: Session = Depends(get_db)):
    """
    Update evaluation metrics for a specific model version.
    """
    try:
        version = update_metrics(db, id, version_id, request.metrics)
        return version
    except ValueError as e:
        logger.error(f"API: Failed to update metrics for model ID {id}, version ID {version_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"API: Unexpected error updating metrics for model ID {id}, version ID {version_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/{id}/deploy", response_model=DeployResponse)
def deploy_model_version(id: int, version_id: int, db: Session = Depends(get_db)):
    """
    Deploy the specified model version.
    """
    try:
        version = deploy_model(db, id, version_id)
        return DeployResponse(
            model_id=id,
            version_id=version_id,
            deployed=True,
            message=f"Model version {version_id} deployed successfully"
        )
    except ValueError as e:
        logger.error(f"API: Failed to deploy model ID {id}, version ID {version_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"API: Unexpected error deploying model ID {id}, version ID {version_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
