import random
from app.schemas.inference import ModelInfo, PredictResponse

# MOCK IMPLEMENTATION - ต่อโมเดลจริงตรงนี้ในอนาคต
MOCK_MODELS = [
    {"name": "default", "version": "1.0", "status": "ready"},
    {"name": "sentiment-analyzer", "version": "0.9", "status": "ready"}
]

def list_models() -> list[ModelInfo]:
    """
    คืนรายชื่อ mock model ทั้งหมด
    """
    return [ModelInfo(**m) for m in MOCK_MODELS]

def predict(input_text: str, model_name: str) -> PredictResponse:
    """
    ทำนายผลจำลองตามข้อมูลที่ได้รับ
    """
    # MOCK IMPLEMENTATION - ต่อโมเดลจริงตรงนี้ในอนาคต
    model_names = [m["name"] for m in MOCK_MODELS]
    if model_name not in model_names:
        raise ValueError("model not found")
    
    # สุ่ม confidence ระหว่าง 0.7-0.99
    confidence = round(random.uniform(0.7, 0.99), 4)
    
    # prediction เป็น string สะท้อนความยาวของ input_text
    prediction = f"Predicted class for text of length {len(input_text)}: SUCCESS"
    
    return PredictResponse(
        model_name=model_name,
        prediction=prediction,
        confidence=confidence
    )
