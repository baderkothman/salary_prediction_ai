from typing import Any

from fastapi import APIRouter, Depends, Query

from backend.app.api.dependencies import get_narrator, get_predictor
from backend.app.core.errors import NarrationUnavailableError, PredictionInputError
from backend.app.schemas.prediction import HealthResponse, NarrateResponse, PredictionResponse
from backend.app.services.narrator import NarratorService
from backend.app.services.predictor import PredictorService, predictor_service

router = APIRouter()


def _predict_query_params(
    experience_level: str = Query(..., max_length=10),
    employment_type: str = Query(..., max_length=10),
    job_title: str = Query(..., max_length=150),
    employee_residence: str = Query(..., max_length=10),
    company_location: str = Query(..., max_length=10),
    company_size: str = Query(..., max_length=5),
    work_year: int = Query(...),
    remote_ratio: int = Query(...),
) -> dict[str, Any]:
    return {
        "experience_level": experience_level,
        "employment_type": employment_type,
        "job_title": job_title,
        "employee_residence": employee_residence,
        "company_location": company_location,
        "company_size": company_size,
        "work_year": work_year,
        "remote_ratio": remote_ratio,
    }


def validate_prediction_inputs(metadata: dict[str, Any], inputs: dict[str, Any]) -> None:
    """Shared by /predict and /narrate so both reject the exact same
    unsupported categories/out-of-range values the exact same way."""
    for field, value in inputs.items():
        domain = metadata["categorical_domains"].get(field)
        if domain is not None and value not in domain:
            raise PredictionInputError(
                code="INVALID_INPUT",
                message=f"Unsupported value for '{field}': {value!r}",
                details={"field": field, "allowed_values": domain},
            )

    year_range = metadata["numeric_ranges"]["work_year"]
    if not (year_range["min"] <= inputs["work_year"] <= year_range["max"]):
        raise PredictionInputError(
            code="INVALID_INPUT",
            message=f"'work_year' must be between {year_range['min']} and {year_range['max']}.",
            details={"field": "work_year", "min": year_range["min"], "max": year_range["max"]},
        )

    remote_allowed = metadata["numeric_ranges"]["remote_ratio"]["allowed_values"]
    if inputs["remote_ratio"] not in remote_allowed:
        raise PredictionInputError(
            code="INVALID_INPUT",
            message=f"'remote_ratio' must be one of {remote_allowed}.",
            details={"field": "remote_ratio", "allowed_values": remote_allowed},
        )


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok" if predictor_service.is_loaded else "degraded",
        model_loaded=predictor_service.is_loaded,
        model_version=predictor_service.metadata["model_version"] if predictor_service.is_loaded else None,
    )


@router.get("/model/info")
def model_info(predictor: PredictorService = Depends(get_predictor)) -> dict:
    metadata = predictor.metadata
    return {
        "model_name": metadata["model_name"],
        "model_version": metadata["model_version"],
        "target": metadata["target"],
        "feature_columns": metadata["feature_columns"],
        "categorical_domains": metadata["categorical_domains"],
        "numeric_ranges": metadata["numeric_ranges"],
        "metrics": metadata["metrics"]["test"],
        "trained_at": metadata["trained_at"],
    }


@router.get("/predict", response_model=PredictionResponse)
def predict(
    inputs: dict[str, Any] = Depends(_predict_query_params),
    predictor: PredictorService = Depends(get_predictor),
) -> PredictionResponse:
    metadata = predictor.metadata
    validate_prediction_inputs(metadata, inputs)

    prediction = predictor.predict_one(inputs)

    return PredictionResponse(
        prediction=round(prediction, 2),
        currency="USD",
        model_version=metadata["model_version"],
        inputs=inputs,
        metadata={"target": metadata["target"]},
    )


@router.get("/narrate", response_model=NarrateResponse)
def narrate(
    inputs: dict[str, Any] = Depends(_predict_query_params),
    predictor: PredictorService = Depends(get_predictor),
    narrator: NarratorService = Depends(get_narrator),
) -> NarrateResponse:
    metadata = predictor.metadata
    validate_prediction_inputs(metadata, inputs)

    predicted_salary = predictor.predict_one(inputs)

    provider_label = "Ollama" if narrator.provider == "ollama" else "Gemini"

    try:
        analysis, error, context = narrator.narrate(inputs, predicted_salary)
    except Exception as exc:  # OllamaUnavailableError / GeminiUnavailableError, imported lazily
        raise NarrationUnavailableError(
            code=f"{narrator.provider.upper()}_UNAVAILABLE",
            message=f"Could not reach {provider_label}: {exc}",
        ) from exc

    if analysis is None:
        raise NarrationUnavailableError(
            code="NARRATIVE_GENERATION_FAILED",
            message=f"{provider_label} did not return a usable analysis after retries: {error}",
        )

    return NarrateResponse(
        prediction=round(predicted_salary, 2),
        currency="USD",
        model_version=metadata["model_version"],
        headline=analysis.headline,
        summary=analysis.summary,
        insights=analysis.insights,
        comparison=analysis.comparison,
        limitations=analysis.limitations,
        chart=analysis.chart.model_dump(),
        supporting_stats=context.get("comparison_group", {}),
        percentile_rank_in_dataset=context.get("percentile_rank_in_dataset"),
    )
