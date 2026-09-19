from fastapi import HTTPException

from backend.app.core.errors import NarrationUnavailableError
from backend.app.services.narrator import NarratorService, narrator_service
from backend.app.services.predictor import PredictorService, predictor_service


def get_predictor() -> PredictorService:
    if not predictor_service.is_loaded:
        raise HTTPException(status_code=503, detail="Model is not loaded.")
    return predictor_service


def get_narrator() -> NarratorService:
    if not narrator_service.is_loaded:
        raise NarrationUnavailableError(
            code="NARRATOR_UNAVAILABLE",
            message="Live narrative generation is not available (missing dataset or not yet loaded).",
        )
    return narrator_service
