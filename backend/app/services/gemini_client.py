"""Cloud LLM narrator for the DEPLOYED backend only, selected via
NARRATOR_PROVIDER=gemini (backend/app/core/config.py). Used when Ollama
isn't reachable -- e.g. Render's servers can't reach a developer's local
machine. The local generation pipeline (scripts/llm_client.py, used by
scripts/run_pipeline.py to populate the published Supabase dataset)
always uses local Ollama regardless of this setting; this is a separate,
backend-only code path.

Deliberately reuses SYSTEM_PROMPT and the SalaryAnalysis/ChartSpec Pydantic
schema from scripts/llm_client.py rather than duplicating them, so both
providers are validated identically and produce interchangeable output.

Privacy note (documented, not silent): when this path is used, the
comparison-group statistics and job attributes in the analysis context
are sent to Google's Gemini API for that request. See README.md's
Deployment section.
"""

import json
import logging
import time

import httpx

from scripts.llm_client import SYSTEM_PROMPT, SalaryAnalysis

logger = logging.getLogger("salary_api")

# Not gemini-3.6-flash (the newest, Google-recommended default at the time
# of writing): confirmed live it was under sustained "high demand" 503s
# across multiple separate test calls. gemini-3.1-flash-lite answered
# reliably and quickly (2-4s) every time it was tried instead, with no
# quality loss for this narration task. Revisit if 3.6-flash's rollout
# congestion settles down.
DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite"
# Every successful live call measured 2-6s. One request took 89s in
# production because 3 outer attempts x up to 3 inner transport retries
# each could ride a slow response close to a 30s timeout before failing
# over. A tighter per-attempt timeout fails a stuck attempt faster,
# capping the worst case without changing retry counts.
DEFAULT_TIMEOUT_SECONDS = 12.0
DEFAULT_MAX_ATTEMPTS = 3
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"

# Confirmed live: Gemini returns a transient 503 ("high demand") often
# enough that retrying once or twice measurably helps -- observed exactly
# this in production and it succeeded on the very next attempt.
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
DEFAULT_TRANSPORT_RETRIES = 2
DEFAULT_BACKOFF_SECONDS = 1.0


class GeminiUnavailableError(RuntimeError):
    """Gemini could not be reached or returned a non-200 response --
    distinct from a malformed generation, mirroring OllamaUnavailableError."""


class GeminiClient:
    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_GEMINI_MODEL,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        transport: httpx.BaseTransport | None = None,
        backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
    ):
        self._api_key = api_key
        self._model = model
        self._timeout = timeout_seconds
        self._transport = transport
        self._backoff_seconds = backoff_seconds

    def _call(self, analysis_context: dict) -> str:
        # Same framing as OllamaClient: a bare JSON blob as the whole
        # prompt reads as "here is JSON" rather than "analyze this."
        user_prompt = (
            "Here are the computed facts for this salary prediction:\n\n"
            f"{json.dumps(analysis_context, indent=2)}\n\n"
            "Write your analysis now, following the JSON schema and rules from the system prompt."
        )
        payload = {
            "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [{"parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                # Confirmed against the real API: this is a reasoning model
                # that otherwise spends ~200+ tokens "thinking" per call with
                # no quality benefit for this constrained JSON task.
                "thinkingConfig": {"thinkingBudget": 0},
            },
        }
        url = f"{GEMINI_API_BASE}/models/{self._model}:generateContent"
        last_error: str | None = None

        for attempt in range(1, DEFAULT_TRANSPORT_RETRIES + 2):
            try:
                with httpx.Client(timeout=self._timeout, transport=self._transport) as client:
                    response = client.post(url, params={"key": self._api_key}, json=payload)
            except httpx.HTTPError as exc:
                last_error = f"Could not reach Gemini: {exc}"
                logger.warning(
                    "Gemini transport attempt %d/%d failed: %s", attempt, DEFAULT_TRANSPORT_RETRIES + 1, last_error
                )
                time.sleep(self._backoff_seconds * attempt)
                continue

            if response.status_code == 200:
                try:
                    body = response.json()
                    return body["candidates"][0]["content"]["parts"][0]["text"]
                except (json.JSONDecodeError, KeyError, IndexError) as exc:
                    raise GeminiUnavailableError(f"Unexpected Gemini response shape: {exc}") from exc

            if response.status_code in RETRYABLE_STATUS_CODES:
                last_error = f"Gemini returned HTTP {response.status_code}: {response.text[:200]}"
                logger.warning(
                    "Gemini transport attempt %d/%d got retryable status %d",
                    attempt,
                    DEFAULT_TRANSPORT_RETRIES + 1,
                    response.status_code,
                )
                time.sleep(self._backoff_seconds * attempt)
                continue

            # Non-retryable (e.g. 400 bad request, 403 bad API key): stop immediately.
            raise GeminiUnavailableError(f"Gemini returned HTTP {response.status_code}: {response.text[:200]}")

        raise GeminiUnavailableError(last_error or "Gemini unavailable after retries")

    def generate_salary_analysis(
        self, analysis_context: dict, max_attempts: int = DEFAULT_MAX_ATTEMPTS
    ) -> tuple[SalaryAnalysis | None, str | None]:
        """Same contract as OllamaClient.generate_salary_analysis: returns
        (analysis, error), raises GeminiUnavailableError for total
        unreachability, retries malformed/invalid generations up to
        max_attempts before giving up."""
        last_error: str | None = None

        for attempt in range(1, max_attempts + 1):
            raw_text = self._call(analysis_context)
            try:
                parsed = json.loads(raw_text)
            except json.JSONDecodeError as exc:
                last_error = f"attempt {attempt}: invalid JSON: {exc}"
                logger.warning(last_error)
                continue

            try:
                analysis = SalaryAnalysis.model_validate(parsed)
            except Exception as exc:  # pydantic.ValidationError; kept broad deliberately
                last_error = f"attempt {attempt}: schema validation failed: {exc}"
                logger.warning(last_error)
                continue

            return analysis, None

        return None, last_error or "exhausted generation attempts"
