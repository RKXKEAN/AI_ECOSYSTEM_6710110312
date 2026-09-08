from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, model_validator


class ModelInfo(BaseModel):
    name: str
    version: str
    status: str


class PredictRequest(BaseModel):
    text: Optional[str] = None
    input_text: Optional[str] = None
    model_version: Optional[str] = None
    model_name: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def populate_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "text" not in data and "input_text" in data:
                data["text"] = data["input_text"]
            elif "input_text" not in data and "text" in data:
                data["input_text"] = data["text"]
            if "model_version" not in data and "model_name" in data:
                if data["model_name"] != "default":
                    data["model_version"] = data["model_name"]
        return data


class PredictResponse(BaseModel):
    job_id: str
    status: str


class InferenceResultResponse(BaseModel):
    job_id: str
    status: str
    input_text: str
    model_version: Optional[str] = None
    result: Optional[Any] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
