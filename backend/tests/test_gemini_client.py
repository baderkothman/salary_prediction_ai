import json

import httpx
import pytest

from backend.app.services.gemini_client import GeminiClient, GeminiUnavailableError

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
    "insights": ["Matches the median for senior Data Scientists."],
    "comparison": "In line with the median of comparable senior Data Scientist roles.",
    "limitations": ["This reflects association in historical data, not causation."],
    "chart": {"type": "bar", "title": "Median salary by experience level", "x": ["senior-level"], "y": [145000.0]},
}


def make_client(handler, **kwargs) -> GeminiClient:
    transport = httpx.MockTransport(handler)
    return GeminiClient(api_key="test-key", transport=transport, **kwargs)


def gemini_response(text: str) -> httpx.Response:
    return httpx.Response(
        200,
        json={"candidates": [{"content": {"parts": [{"text": text}]}, "finishReason": "STOP"}]},
    )


def test_valid_response_is_parsed_and_validated():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["key"] == "test-key"
        return gemini_response(json.dumps(VALID_ANALYSIS))

    client = make_client(handler)
    analysis, error = client.generate_salary_analysis(SAMPLE_CONTEXT)

    assert error is None
    assert analysis.headline == VALID_ANALYSIS["headline"]
    assert analysis.chart.type == "bar"


def test_malformed_json_is_retried_then_marked_failed():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return gemini_response("not valid json{{")

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
            return gemini_response("{broken")
        return gemini_response(json.dumps(VALID_ANALYSIS))

    client = make_client(handler)
    analysis, error = client.generate_salary_analysis(SAMPLE_CONTEXT, max_attempts=3)

    assert error is None
    assert analysis is not None
    assert calls["n"] == 2


def test_invalid_chart_type_is_rejected():
    bad = {**VALID_ANALYSIS, "chart": {**VALID_ANALYSIS["chart"], "type": "pie"}}

    def handler(request: httpx.Request) -> httpx.Response:
        return gemini_response(json.dumps(bad))

    client = make_client(handler)
    analysis, error = client.generate_salary_analysis(SAMPLE_CONTEXT, max_attempts=1)

    assert analysis is None
    assert "schema validation failed" in error


def test_gemini_unreachable_raises_unavailable_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    client = make_client(handler)
    with pytest.raises(GeminiUnavailableError):
        client.generate_salary_analysis(SAMPLE_CONTEXT)


def test_gemini_non_200_raises_unavailable_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="model overloaded")

    client = make_client(handler)
    with pytest.raises(GeminiUnavailableError):
        client.generate_salary_analysis(SAMPLE_CONTEXT)


def test_unexpected_response_shape_raises_unavailable_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"candidates": []})

    client = make_client(handler)
    with pytest.raises(GeminiUnavailableError):
        client.generate_salary_analysis(SAMPLE_CONTEXT)
