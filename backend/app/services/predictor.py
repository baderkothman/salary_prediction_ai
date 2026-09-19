"""Loads the serialized preprocessing+model Pipeline and its metadata.

Deliberately has zero import dependency on the `ml` package: everything the
API needs to know about the model's schema (feature columns, categorical
domains, numeric ranges) is read from model_metadata.json at runtime. This
keeps the backend independently deployable with just two data files plus
this code -- no training pipeline required at deploy time.
"""

import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from backend.app.core.config import settings


class ModelNotLoadedError(RuntimeError):
    pass


class PredictorService:
    def __init__(self, model_path: Path, metadata_path: Path):
        self._model_path = model_path
        self._metadata_path = metadata_path
        self._pipeline = None
        self._metadata: dict[str, Any] | None = None

    def load(self) -> None:
        if not self._model_path.exists():
            raise FileNotFoundError(f"Model artifact not found at {self._model_path}")
        if not self._metadata_path.exists():
            raise FileNotFoundError(f"Model metadata not found at {self._metadata_path}")
        self._pipeline = joblib.load(self._model_path)
        self._metadata = json.loads(self._metadata_path.read_text())

    @property
    def is_loaded(self) -> bool:
        return self._pipeline is not None and self._metadata is not None

    @property
    def metadata(self) -> dict[str, Any]:
        if self._metadata is None:
            raise ModelNotLoadedError("Model metadata is not loaded.")
        return self._metadata

    def predict_one(self, inputs: dict[str, Any]) -> float:
        if self._pipeline is None:
            raise ModelNotLoadedError("Model is not loaded.")
        row = pd.DataFrame([inputs])[self._metadata["feature_columns"]]
        prediction = self._pipeline.predict(row)[0]
        return float(prediction)


predictor_service = PredictorService(settings.model_path, settings.model_metadata_path)
