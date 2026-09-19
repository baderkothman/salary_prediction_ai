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


class ChartSpecResponse(BaseModel):
    type: str
    title: str
    x: list[str]
    y: list[float]


class NarrateResponse(BaseModel):
    prediction: float
    currency: str = "USD"
    model_version: str
    headline: str
    summary: str
    insights: list[str]
    comparison: str
    limitations: list[str]
    chart: ChartSpecResponse
    supporting_stats: dict
    percentile_rank_in_dataset: float | None = None
