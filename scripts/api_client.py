"""Robust client for calling the FastAPI /predict endpoint.

Used standalone (this is prd.md FR-06: a script that calls the API without
unhandled failures) and reused by scripts/run_pipeline.py in a later phase
to fetch predictions for every distinct observed feature tuple.

Retry policy: only transient failures are retried (connection errors,
timeouts, 5xx) with linear backoff, bounded by max_retries. Deterministic
4xx responses (bad input) are never retried -- retrying them would just
waste time reproducing the same validation failure.
"""

import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger("api_client")

DEFAULT_TIMEOUT_SECONDS = 15.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_SECONDS = 1.0
RETRYABLE_STATUS_CODES = {500, 502, 503, 504}
REQUIRED_RESPONSE_FIELDS = ("prediction", "currency", "model_version")


@dataclass
class PredictionOutcome:
    inputs: dict[str, Any]
    success: bool
    status_code: int | None = None
    response_body: dict | None = None
    error: str | None = None


class SalaryApiClient:
    def __init__(
        self,
        base_url: str,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
        transport: httpx.BaseTransport | None = None,
    ):
        self._base_url = base_url.rstrip("/")
        self._timeout = httpx.Timeout(timeout_seconds)
        self._max_retries = max_retries
        self._backoff_seconds = backoff_seconds
        self._transport = transport

    def predict(self, inputs: dict[str, Any]) -> PredictionOutcome:
        last_error: str | None = None
        last_status: int | None = None

        for attempt in range(1, self._max_retries + 2):
            try:
                with httpx.Client(timeout=self._timeout, transport=self._transport) as client:
                    response = client.get(f"{self._base_url}/predict", params=inputs)
            except httpx.HTTPError as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                logger.warning(
                    "Attempt %d/%d transport error for inputs=%s: %s",
                    attempt, self._max_retries + 1, inputs, last_error,
                )
                self._sleep_backoff(attempt)
                continue

            last_status = response.status_code

            if response.status_code == 200:
                return self._parse_success(inputs, response)

            if response.status_code in RETRYABLE_STATUS_CODES:
                last_error = f"server error {response.status_code}"
                logger.warning(
                    "Attempt %d/%d got retryable status %d for inputs=%s",
                    attempt, self._max_retries + 1, response.status_code, inputs,
                )
                self._sleep_backoff(attempt)
                continue

            # Deterministic 4xx (or any other non-retryable status): stop immediately.
            return PredictionOutcome(
                inputs=inputs,
                success=False,
                status_code=response.status_code,
                response_body=self._try_parse_json(response),
                error=f"client error {response.status_code}",
            )

        return PredictionOutcome(inputs=inputs, success=False, status_code=last_status, error=last_error or "exhausted retries")

    @staticmethod
    def _try_parse_json(response: httpx.Response) -> dict | None:
        try:
            return response.json()
        except json.JSONDecodeError:
            return None

    def _parse_success(self, inputs: dict[str, Any], response: httpx.Response) -> PredictionOutcome:
        body = self._try_parse_json(response)
        if body is None:
            return PredictionOutcome(
                inputs=inputs, success=False, status_code=response.status_code, error="malformed JSON response"
            )

        missing = [field for field in REQUIRED_RESPONSE_FIELDS if field not in body]
        if missing:
            return PredictionOutcome(
                inputs=inputs,
                success=False,
                status_code=response.status_code,
                response_body=body,
                error=f"response missing fields: {missing}",
            )

        return PredictionOutcome(inputs=inputs, success=True, status_code=response.status_code, response_body=body)

    def _sleep_backoff(self, attempt: int) -> None:
        time.sleep(self._backoff_seconds * attempt)


def run_batch(client: SalaryApiClient, input_rows: list[dict[str, Any]]) -> list[PredictionOutcome]:
    """Call predict() for every row. A single unexpected failure never stops
    the batch -- prd.md FR-06: 'Never terminate the entire batch because one
    request failed.'"""
    outcomes: list[PredictionOutcome] = []
    for row in input_rows:
        try:
            outcome = client.predict(row)
        except Exception as exc:  # last-resort guard; predict() is designed not to raise
            logger.exception("Unexpected error calling predict for inputs=%s", row)
            outcome = PredictionOutcome(inputs=row, success=False, error=f"unexpected error: {exc}")
        outcomes.append(outcome)
    return outcomes


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    base_url = os.environ.get("LOCAL_API_BASE_URL", "http://127.0.0.1:8000")
    client = SalaryApiClient(base_url=base_url)

    sample_inputs = [
        {
            "experience_level": "SE",
            "employment_type": "FT",
            "job_title": "Data Scientist",
            "employee_residence": "US",
            "company_location": "US",
            "company_size": "M",
            "work_year": 2022,
            "remote_ratio": 100,
        },
        {
            "experience_level": "NOT_REAL",
            "employment_type": "FT",
            "job_title": "Data Scientist",
            "employee_residence": "US",
            "company_location": "US",
            "company_size": "M",
            "work_year": 2022,
            "remote_ratio": 100,
        },
    ]

    outcomes = run_batch(client, sample_inputs)
    succeeded = [o for o in outcomes if o.success]
    failed = [o for o in outcomes if not o.success]

    print(f"{len(succeeded)} succeeded, {len(failed)} failed")
    for outcome in failed:
        print(f"FAILED: {outcome.inputs} -> {outcome.error}")

    if failed:
        from pathlib import Path

        failures_path = Path("ml/artifacts/reports/api_client_failures.json")
        failures_path.parent.mkdir(parents=True, exist_ok=True)
        failures_path.write_text(
            json.dumps([{"inputs": o.inputs, "status_code": o.status_code, "error": o.error} for o in failed], indent=2)
        )
        print(f"Wrote failed inputs to {failures_path}")


if __name__ == "__main__":
    main()
