import json

import httpx
import pytest

from scripts.llm_client import OllamaClient, OllamaUnavailableError

SAMPLE_CONTEXT = {
    "prediction_usd": 145000.0,
    "inputs": {"experience_level": "SE", "job_title": "Data Scientist"},
    "comparison_group": {
        "description": "Data Scientist roles at senior-level",
        "sample_size": 10,
        "mean_salary_usd": 145000.0,
        "median_salary_usd": 145000.0,
        "p25_salary_usd": 120000.0,
        "p75_salary_usd": 170000.0,
    },
    "percentile_rank_in_dataset": 62.5,
    "chart_data_by_experience_level": [{"label": "senior-level", "value": 145000.0}],
}

VALID_ANALYSIS = {
    "headline": "Prediction sits at the peer median",
    "summary": "This senior Data Scientist prediction of $145,000 matches the peer median for similar roles.",
    "insights": ["Matches the median for senior Data Scientists.", "Sits above the 25th percentile peer salary."],
    "comparison": "The prediction is in line with the median of comparable senior Data Scientist roles.",
    "limitations": ["This reflects association in historical data, not a guarantee of causation."],
    "chart": {"type": "bar", "title": "Median salary by experience level", "x": ["senior-level"], "y": [145000.0]},
}


def make_client(handler, **kwargs) -> OllamaClient:
    transport = httpx.MockTransport(handler)
    kwargs.setdefault("backoff_seconds", 0.001)
    return OllamaClient(base_url="http://testserver", transport=transport, **kwargs)


def ollama_response(body_dict: dict) -> httpx.Response:
    return httpx.Response(200, json={"model": "qwen3:4b", "response": json.dumps(body_dict), "done": True})


def test_valid_response_is_parsed_and_validated():
    def handler(request: httpx.Request) -> httpx.Response:
        return ollama_response(VALID_ANALYSIS)

    client = make_client(handler)
    analysis, error = client.generate_salary_analysis(SAMPLE_CONTEXT)

    assert error is None
    assert analysis.headline == VALID_ANALYSIS["headline"]
    assert analysis.chart.type == "bar"


def test_malformed_json_is_retried_then_marked_failed():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, json={"model": "x", "response": "not valid json{{", "done": True})

    client = make_client(handler)
    analysis, error = client.generate_salary_analysis(SAMPLE_CONTEXT, max_attempts=3)

    assert analysis is None
    assert "invalid JSON" in error
    assert calls["n"] == 3


def test_recovers_after_one_malformed_attempt():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(200, json={"model": "x", "response": "{broken", "done": True})
        return ollama_response(VALID_ANALYSIS)

    client = make_client(handler)
    analysis, error = client.generate_salary_analysis(SAMPLE_CONTEXT, max_attempts=3)

    assert error is None
    assert analysis is not None
    assert calls["n"] == 2


def test_invalid_chart_type_is_rejected():
    bad = {**VALID_ANALYSIS, "chart": {**VALID_ANALYSIS["chart"], "type": "pie"}}

    def handler(request: httpx.Request) -> httpx.Response:
        return ollama_response(bad)

    client = make_client(handler)
    analysis, error = client.generate_salary_analysis(SAMPLE_CONTEXT, max_attempts=1)

    assert analysis is None
    assert "schema validation failed" in error


def test_mismatched_chart_axis_lengths_rejected():
    bad = {**VALID_ANALYSIS, "chart": {**VALID_ANALYSIS["chart"], "x": ["a", "b"], "y": [1]}}

    def handler(request: httpx.Request) -> httpx.Response:
        return ollama_response(bad)

    client = make_client(handler)
    analysis, error = client.generate_salary_analysis(SAMPLE_CONTEXT, max_attempts=1)

    assert analysis is None
    assert "schema validation failed" in error


def test_bare_string_limitation_is_coerced_to_single_item_list():
    # Observed against the real local model: a single limitation is often
    # returned as a bare string instead of a one-item list.
    quirky = {**VALID_ANALYSIS, "limitations": "Small sample size limits generalizability."}

    def handler(request: httpx.Request) -> httpx.Response:
        return ollama_response(quirky)

    client = make_client(handler)
    analysis, error = client.generate_salary_analysis(SAMPLE_CONTEXT, max_attempts=1)

    assert error is None
    assert analysis.limitations == ["Small sample size limits generalizability."]


def test_too_many_insights_rejected():
    bad = {**VALID_ANALYSIS, "insights": ["x"] * 10}

    def handler(request: httpx.Request) -> httpx.Response:
        return ollama_response(bad)

    client = make_client(handler)
    analysis, error = client.generate_salary_analysis(SAMPLE_CONTEXT, max_attempts=1)

    assert analysis is None
    assert "schema validation failed" in error


def test_ollama_unreachable_raises_unavailable_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    client = make_client(handler)
    with pytest.raises(OllamaUnavailableError):
        client.generate_salary_analysis(SAMPLE_CONTEXT)


def test_ollama_non_200_raises_unavailable_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="internal error")

    client = make_client(handler)
    with pytest.raises(OllamaUnavailableError):
        client.generate_salary_analysis(SAMPLE_CONTEXT)


def test_transient_503_is_retried_then_succeeds():
    # Reproduces a real failure observed live: Ollama/Gemini-style APIs can
    # return a transient 503 that succeeds on the very next attempt.
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 2:
            return httpx.Response(503, text="busy")
        return ollama_response(VALID_ANALYSIS)

    client = make_client(handler)
    analysis, error = client.generate_salary_analysis(SAMPLE_CONTEXT)

    assert error is None
    assert analysis.headline == VALID_ANALYSIS["headline"]
    assert calls["n"] == 2


def test_persistent_5xx_exhausts_transport_retries_then_raises():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(503, text="still busy")

    client = make_client(handler)
    with pytest.raises(OllamaUnavailableError):
        client.generate_salary_analysis(SAMPLE_CONTEXT)

    assert calls["n"] == 3  # initial attempt + 2 transport retries


def test_non_retryable_4xx_is_not_retried():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(400, text="bad request")

    client = make_client(handler)
    with pytest.raises(OllamaUnavailableError):
        client.generate_salary_analysis(SAMPLE_CONTEXT)

    assert calls["n"] == 1
