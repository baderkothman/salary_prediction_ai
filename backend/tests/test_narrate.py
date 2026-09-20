import json
from pathlib import Path

import httpx
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.app.api.dependencies import get_narrator
from backend.app.core.errors import NarrationUnavailableError
from backend.app.main import app
from backend.app.services.gemini_client import GeminiClient
from backend.app.services.narrator import NarratorService
from backend.app.services.predictor import predictor_service
from scripts.build_context import build_analysis_context
from scripts.llm_client import OllamaClient

VALID_ANALYSIS_JSON = {
    "headline": "Above the peer median",
    "summary": "This prediction sits above the peer median for comparable senior roles.",
    "insights": ["Matches senior-level compensation trends."],
    "comparison": "Above the median of comparable roles.",
    "limitations": ["This reflects association, not causation."],
    "chart": {"type": "bar", "title": "Median by level", "x": ["SE"], "y": [140000]},
}

VALID_PARAMS = {
    "experience_level": "SE",
    "employment_type": "FT",
    "job_title": "Data Scientist",
    "employee_residence": "US",
    "company_location": "US",
    "company_size": "M",
    "work_year": 2022,
    "remote_ratio": 100,
}


def make_fake_narrator(handler) -> NarratorService:
    narrator = NarratorService(
        dataset_path=Path("unused"),
        provider="ollama",
        ollama_base_url="http://testserver",
        ollama_model="test",
        gemini_api_key="",
        gemini_model="test",
    )
    narrator._df = pd.read_csv("ml/data/processed/salaries_clean.csv")
    narrator._build_context = build_analysis_context
    narrator._client = OllamaClient(base_url="http://testserver", transport=httpx.MockTransport(handler))
    return narrator


def make_fake_gemini_narrator(handler) -> NarratorService:
    narrator = NarratorService(
        dataset_path=Path("unused"),
        provider="gemini",
        ollama_base_url="unused",
        ollama_model="unused",
        gemini_api_key="test-key",
        gemini_model="test",
    )
    narrator._df = pd.read_csv("ml/data/processed/salaries_clean.csv")
    narrator._build_context = build_analysis_context
    narrator._client = GeminiClient(api_key="test-key", transport=httpx.MockTransport(handler))
    return narrator


def ollama_response(body: dict) -> httpx.Response:
    return httpx.Response(200, json={"model": "test", "response": json.dumps(body), "done": True})


def gemini_response(body: dict) -> httpx.Response:
    return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": json.dumps(body)}]}}]})


@pytest.fixture(scope="module", autouse=True)
def loaded_predictor():
    if not predictor_service.is_loaded:
        predictor_service.load()


@pytest.fixture
def client():
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.pop(get_narrator, None)


def test_narrate_valid_request_returns_narrative(client):
    app.dependency_overrides[get_narrator] = lambda: make_fake_narrator(lambda r: ollama_response(VALID_ANALYSIS_JSON))

    response = client.get("/narrate", params=VALID_PARAMS)

    assert response.status_code == 200
    body = response.json()
    assert body["headline"] == VALID_ANALYSIS_JSON["headline"]
    assert body["prediction"] > 0
    assert body["chart"]["type"] == "bar"
    assert "sample_size" in body["supporting_stats"]


def test_narrate_ollama_unreachable_returns_503(client):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    app.dependency_overrides[get_narrator] = lambda: make_fake_narrator(handler)

    response = client.get("/narrate", params=VALID_PARAMS)

    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] == "OLLAMA_UNAVAILABLE"


def test_narrate_persistent_malformed_generation_returns_503(client):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"model": "test", "response": "not valid json", "done": True})

    app.dependency_overrides[get_narrator] = lambda: make_fake_narrator(handler)

    response = client.get("/narrate", params=VALID_PARAMS)

    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] == "NARRATIVE_GENERATION_FAILED"


def test_narrate_invalid_input_returns_422_without_calling_ollama(client):
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return ollama_response(VALID_ANALYSIS_JSON)

    app.dependency_overrides[get_narrator] = lambda: make_fake_narrator(handler)

    bad_params = {**VALID_PARAMS, "experience_level": "ZZ"}
    response = client.get("/narrate", params=bad_params)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_INPUT"
    assert calls["n"] == 0  # input validation must reject before ever calling Ollama


def test_narrate_gemini_provider_returns_narrative(client):
    app.dependency_overrides[get_narrator] = lambda: make_fake_gemini_narrator(
        lambda r: gemini_response(VALID_ANALYSIS_JSON)
    )

    response = client.get("/narrate", params=VALID_PARAMS)

    assert response.status_code == 200
    assert response.json()["headline"] == VALID_ANALYSIS_JSON["headline"]


def test_narrate_gemini_unreachable_returns_503_with_gemini_code(client):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    app.dependency_overrides[get_narrator] = lambda: make_fake_gemini_narrator(handler)

    response = client.get("/narrate", params=VALID_PARAMS)

    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] == "GEMINI_UNAVAILABLE"
    assert "Gemini" in body["error"]["message"]


def test_narrate_returns_503_when_narrator_not_loaded(client):
    def raise_unavailable():
        raise NarrationUnavailableError(code="NARRATOR_UNAVAILABLE", message="not loaded")

    app.dependency_overrides[get_narrator] = raise_unavailable

    response = client.get("/narrate", params=VALID_PARAMS)

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "NARRATOR_UNAVAILABLE"
