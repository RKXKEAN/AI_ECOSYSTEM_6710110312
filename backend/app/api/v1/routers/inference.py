from fastapi import APIRouter, HTTPException
from app.schemas.inference import ModelInfo, PredictRequest, PredictResponse
from app.services.inference_service import list_models, predict

router = APIRouter(prefix="/inference", tags=["Inference"])

@router.get("/models", response_model=list[ModelInfo])
def get_models():
    """
    ดึงรายชื่อ model ทั้งหมด
    """
    return list_models()

@router.post("/predict", response_model=PredictResponse)
def post_predict(request: PredictRequest):
    """
    ทำนายผลด้วยโมเดลที่เลือก
    """
    try:
        return predict(request.input_text, request.model_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
