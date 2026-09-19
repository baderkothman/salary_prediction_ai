"""Calls the local Ollama model to turn a precomputed analysis context into
a narrative. The LLM never sees raw data or is asked to calculate anything
(essentials.md #8) -- scripts/build_context.py already computed every
number in the prompt.

Schema note: this merges the master implementation prompt's field names
(headline, summary, insights, comparison, chart{type,title,x,y}) with
prd.md FR-08's explicit requirement for a `limitations[]` array, which is
also a named acceptance criterion and is required by security.md's
"enforce maximum number of insights/data points" rule. Both are satisfied
by keeping all of these fields together rather than picking one source
over the other.
"""

import json
import logging

import httpx
from pydantic import BaseModel, Field, field_validator, model_validator

logger = logging.getLogger("llm_client")

DEFAULT_OLLAMA_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_OLLAMA_MODEL = "llama3.2:latest"
DEFAULT_TIMEOUT_SECONDS = 60.0
DEFAULT_MAX_ATTEMPTS = 3

ALLOWED_CHART_TYPES = {"bar", "horizontal_bar", "line"}
MAX_INSIGHTS = 5
MAX_LIMITATIONS = 4
MAX_CHART_POINTS = 12
MAX_HEADLINE_LEN = 150
MAX_TEXT_LEN = 500
MAX_LIST_ITEM_LEN = 240

PROMPT_VERSION = "v1"

SYSTEM_PROMPT = """You are a careful salary data analyst. You will be given a JSON object with:
- prediction_usd: a predicted salary
- inputs: the job attributes that produced it
- comparison_group: a peer group with precomputed sample_size, mean_salary_usd, median_salary_usd, p25_salary_usd, p75_salary_usd
- percentile_rank_in_dataset: the prediction's percentile rank across the whole dataset
- chart_data_by_experience_level: precomputed [{"label", "value"}] points

Rules you must follow exactly:
1. Use ONLY the numbers given to you. Never invent, estimate, or recalculate any statistic not present in the input.
2. Explain the prediction's RELATIVE position (above/below the peer median), not just the absolute number.
3. Reference at least two of the supplied job attributes when the data supports it.
4. Add a limitation noting small sample size if comparison_group.sample_size < 15, and always note that the dataset shows association, not causation -- never claim one factor "causes" a higher salary.
5. Avoid generic filler sentences that don't reference the supplied facts.
6. Choose exactly one chart type from: bar, horizontal_bar, line.
7. Return ONLY a single JSON object, no prose outside the JSON, matching exactly this shape:
{"headline": "short one-line takeaway", "summary": "2-4 sentences grounded in the supplied numbers", "insights": ["short factual insight"], "comparison": "one sentence comparing the prediction to the peer group", "limitations": ["short limitation statement"], "chart": {"type": "bar", "title": "chart title", "x": ["label1"], "y": [0]}}
"""


class ChartSpec(BaseModel):
    type: str
    title: str = Field(max_length=120)
    x: list[str] = Field(max_length=MAX_CHART_POINTS)
    y: list[float] = Field(max_length=MAX_CHART_POINTS)

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        if value not in ALLOWED_CHART_TYPES:
            raise ValueError(f"chart.type must be one of {sorted(ALLOWED_CHART_TYPES)}, got {value!r}")
        return value

    @model_validator(mode="after")
    def validate_matching_lengths(self) -> "ChartSpec":
        if len(self.x) != len(self.y):
            raise ValueError("chart.x and chart.y must have the same length")
        if len(self.x) == 0:
            raise ValueError("chart must contain at least one data point")
        return self


class SalaryAnalysis(BaseModel):
    headline: str = Field(max_length=MAX_HEADLINE_LEN)
    summary: str = Field(max_length=MAX_TEXT_LEN)
    insights: list[str] = Field(max_length=MAX_INSIGHTS)
    comparison: str = Field(max_length=MAX_TEXT_LEN)
    limitations: list[str] = Field(max_length=MAX_LIMITATIONS)
    chart: ChartSpec

    @field_validator("insights", "limitations", mode="before")
    @classmethod
    def coerce_single_string_to_list(cls, value):
        # Observed against the real model (llama3.2): when there's exactly
        # one item, it's frequently returned as a bare string instead of a
        # single-item list. That's a reasonable near-miss shape worth
        # normalizing rather than burning a retry attempt over.
        if isinstance(value, str):
            return [value]
        return value

    @field_validator("insights", "limitations")
    @classmethod
    def validate_item_lengths(cls, values: list[str]) -> list[str]:
        for item in values:
            if len(item) > MAX_LIST_ITEM_LEN:
                raise ValueError(f"list item exceeds {MAX_LIST_ITEM_LEN} characters")
        return values


class OllamaUnavailableError(RuntimeError):
    """Ollama could not be reached or returned a non-200 response. This is
    distinct from a malformed generation -- callers should apply the
    documented fallback (mark the record as failed, do not crash the run)
    rather than treat it as a retryable content problem."""


class OllamaClient:
    def __init__(
        self,
        base_url: str = DEFAULT_OLLAMA_BASE_URL,
        model: str = DEFAULT_OLLAMA_MODEL,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        transport: httpx.BaseTransport | None = None,
    ):
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout_seconds
        self._transport = transport

    def _call(self, analysis_context: dict) -> str:
        # A bare JSON blob as the entire prompt (confirmed against the real
        # server) leads the model to just echo the input back instead of
        # analyzing it -- it needs an explicit instruction sentence telling
        # it what to do with the facts.
        user_prompt = (
            "Here are the computed facts for this salary prediction:\n\n"
            f"{json.dumps(analysis_context, indent=2)}\n\n"
            "Write your analysis now, following the JSON schema and rules from the system prompt."
        )
        payload = {
            "model": self._model,
            "system": SYSTEM_PROMPT,
            "prompt": user_prompt,
            "format": "json",
            "stream": False,
            # Reasoning-capable models (e.g. qwen3) otherwise put their
            # entire output in a separate "thinking" field and leave
            # "response" empty -- confirmed against the real local server,
            # not assumed from docs.
            "think": False,
        }
        try:
            with httpx.Client(timeout=self._timeout, transport=self._transport) as client:
                response = client.post(f"{self._base_url}/api/generate", json=payload)
        except httpx.HTTPError as exc:
            raise OllamaUnavailableError(f"Could not reach Ollama at {self._base_url}: {exc}") from exc

        if response.status_code != 200:
            raise OllamaUnavailableError(f"Ollama returned HTTP {response.status_code}: {response.text[:200]}")

        try:
            body = response.json()
        except json.JSONDecodeError as exc:
            raise OllamaUnavailableError(f"Ollama response was not JSON: {exc}") from exc

        return body.get("response", "")

    def generate_salary_analysis(
        self, analysis_context: dict, max_attempts: int = DEFAULT_MAX_ATTEMPTS
    ) -> tuple[SalaryAnalysis | None, str | None]:
        """Returns (analysis, error) -- exactly one is None.

        Raises OllamaUnavailableError if Ollama itself cannot be reached
        (the caller should apply the documented fallback). Malformed or
        schema-invalid generations are retried up to max_attempts and, if
        still bad, reported back as a failure rather than raised -- prd.md
        FR-08 / plan.md: 'mark persistent malformed generations as failed
        instead of storing invalid JSON.'
        """
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
