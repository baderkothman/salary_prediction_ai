from fastapi import HTTPException

from backend.app.services.predictor import PredictorService, predictor_service


def get_predictor() -> PredictorService:
    if not predictor_service.is_loaded:
        raise HTTPException(status_code=503, detail="Model is not loaded.")
    return predictor_service
