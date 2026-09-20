"""Wraps the local generation pipeline's context-building plus a
narrator client (Ollama or Gemini) for the live /narrate endpoint.

This is a deliberate, documented expansion of the backend's dependency
footprint beyond the core prediction service. architecture.md invariant
#8 ("the deployed API needs nothing but the model artifact") still holds
for /health, /model/info, and /predict -- they never import this module.
/narrate additionally needs the cleaned dataset (for comparison-group
statistics) and a reachable narrator provider, and is designed to
degrade to a clean, documented failure rather than crash the whole
service when either isn't available -- see is_loaded and the
provider-specific *UnavailableError re-raise in narrate().

Provider selection (NARRATOR_PROVIDER, backend/app/core/config.py):
- "ollama" (default): matches local dev, where Ollama runs alongside the
  API on the same machine. Used by scripts/run_pipeline.py too.
- "gemini": for deployments (e.g. Render) that can't reach a developer's
  local Ollama instance. Sends the analysis context to Google's API for
  that request -- see backend/app/services/gemini_client.py and
  README.md's Deployment section for the privacy note.
"""

import logging
from pathlib import Path
from typing import Any

import pandas as pd

from backend.app.core.config import settings

logger = logging.getLogger("salary_api")


class NarratorService:
    def __init__(
        self,
        dataset_path: Path,
        provider: str,
        ollama_base_url: str,
        ollama_model: str,
        gemini_api_key: str,
        gemini_model: str,
    ):
        self._dataset_path = dataset_path
        self._provider = provider
        self._ollama_base_url = ollama_base_url
        self._ollama_model = ollama_model
        self._gemini_api_key = gemini_api_key
        self._gemini_model = gemini_model
        self._df: pd.DataFrame | None = None
        self._client = None

    @property
    def provider(self) -> str:
        return self._provider

    def load(self) -> None:
        # Imported lazily so a deployment that omits scripts/ (e.g. a
        # minimal predict-only container) can still boot and serve
        # /predict -- only constructing a NarratorService fails, and the
        # lifespan handler that calls this already catches and logs it.
        from scripts.build_context import build_analysis_context

        if not self._dataset_path.exists():
            raise FileNotFoundError(f"Cleaned dataset not found at {self._dataset_path}")

        self._df = pd.read_csv(self._dataset_path)
        self._build_context = build_analysis_context

        if self._provider == "gemini":
            from backend.app.services.gemini_client import GeminiClient

            if not self._gemini_api_key:
                raise RuntimeError("NARRATOR_PROVIDER=gemini requires GEMINI_API_KEY to be set.")
            self._client = GeminiClient(api_key=self._gemini_api_key, model=self._gemini_model)
        else:
            from scripts.llm_client import OllamaClient

            self._client = OllamaClient(base_url=self._ollama_base_url, model=self._ollama_model)

    @property
    def is_loaded(self) -> bool:
        return self._df is not None and self._client is not None

    def narrate(self, inputs: dict[str, Any], predicted_salary: float):
        """Returns (analysis, error, context). Raises OllamaUnavailableError
        or GeminiUnavailableError (matching self._provider) if the provider
        itself can't be reached -- the route maps that to a 503."""
        if not self.is_loaded:
            raise RuntimeError("Narrator service is not loaded.")
        context = self._build_context(self._df, inputs, predicted_salary)
        analysis, error = self._client.generate_salary_analysis(context)
        return analysis, error, context


narrator_service = NarratorService(
    dataset_path=settings.processed_dataset_path,
    provider=settings.narrator_provider,
    ollama_base_url=settings.ollama_base_url,
    ollama_model=settings.ollama_model,
    gemini_api_key=settings.gemini_api_key,
    gemini_model=settings.gemini_model,
)
