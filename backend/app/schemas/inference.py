from pydantic import BaseModel

class PredictRequest(BaseModel):
    input_text: str
    model_name: str = "default"

class PredictResponse(BaseModel):
    model_name: str
    prediction: str
    confidence: float

class ModelInfo(BaseModel):
    name: str
    version: str
    status: str
