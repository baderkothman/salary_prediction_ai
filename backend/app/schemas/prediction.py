from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_version: str | None = None


class PredictionResponse(BaseModel):
    prediction: float
    currency: str = "USD"
    model_version: str
    inputs: dict
    metadata: dict
