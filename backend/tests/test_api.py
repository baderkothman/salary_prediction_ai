import json

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.predictor import predictor_service


@pytest.fixture(scope="module", autouse=True)
def loaded_predictor():
    if not predictor_service.is_loaded:
        predictor_service.load()
    return predictor_service


@pytest.fixture(scope="module")
def client():
    # raise_server_exceptions=False so an unhandled 500 is asserted as a
    # JSON response (what a real caller sees) instead of re-raised for
    # local debugging, which is TestClient's default.
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture(scope="module")
def sample_valid_params(loaded_predictor):
    metadata = loaded_predictor.metadata
    return {
        "experience_level": metadata["categorical_domains"]["experience_level"][0],
        "employment_type": metadata["categorical_domains"]["employment_type"][0],
        "job_title": metadata["categorical_domains"]["job_title"][0],
        "employee_residence": metadata["categorical_domains"]["employee_residence"][0],
        "company_location": metadata["categorical_domains"]["company_location"][0],
        "company_size": metadata["categorical_domains"]["company_size"][0],
        "work_year": metadata["numeric_ranges"]["work_year"]["max"],
        "remote_ratio": metadata["numeric_ranges"]["remote_ratio"]["allowed_values"][0],
    }


def test_health_reports_model_loaded(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["model_loaded"] is True
    assert body["model_version"]


def test_model_info_returns_metadata(client):
    response = client.get("/model/info")
    assert response.status_code == 200
    body = response.json()
    for key in ("model_name", "model_version", "target", "feature_columns", "categorical_domains", "numeric_ranges", "metrics"):
        assert key in body
    assert "mae" in body["metrics"]
    assert "rmse" in body["metrics"]
    assert "r2" in body["metrics"]


def test_predict_valid_request_returns_structured_response(client, sample_valid_params):
    response = client.get("/predict", params=sample_valid_params)
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["prediction"], (int, float))
    assert body["prediction"] >= 0
    assert body["currency"] == "USD"
    assert body["model_version"]
    assert body["inputs"]["experience_level"] == sample_valid_params["experience_level"]


def test_predict_missing_parameter_returns_422(client, sample_valid_params):
    params = dict(sample_valid_params)
    del params["job_title"]
    response = client.get("/predict", params=params)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_predict_unsupported_category_returns_422(client, sample_valid_params):
    params = dict(sample_valid_params)
    params["experience_level"] = "ZZ"  # short enough to pass FastAPI's max_length, but not a real code
    response = client.get("/predict", params=params)
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "INVALID_INPUT"
    assert body["error"]["details"]["field"] == "experience_level"


def test_predict_invalid_numeric_returns_422(client, sample_valid_params):
    params = dict(sample_valid_params)
    params["remote_ratio"] = 25  # not one of {0, 50, 100}
    response = client.get("/predict", params=params)
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "INVALID_INPUT"
    assert body["error"]["details"]["field"] == "remote_ratio"


def test_predict_non_numeric_work_year_returns_422(client, sample_valid_params):
    params = dict(sample_valid_params)
    params["work_year"] = "not-a-year"
    response = client.get("/predict", params=params)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_no_stack_trace_leaks_on_unexpected_error(client, sample_valid_params, monkeypatch):
    def boom(self, inputs):
        raise RuntimeError("simulated internal failure with a secret path /etc/passwd")

    monkeypatch.setattr(type(predictor_service), "predict_one", boom)
    response = client.get("/predict", params=sample_valid_params)
    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "INTERNAL_ERROR"
    assert "secret" not in json.dumps(body)
    assert "Traceback" not in json.dumps(body)
