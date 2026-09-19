import json

import httpx
import pytest

from scripts.api_client import SalaryApiClient, run_batch

VALID_INPUTS = {
    "experience_level": "SE",
    "employment_type": "FT",
    "job_title": "Data Scientist",
    "employee_residence": "US",
    "company_location": "US",
    "company_size": "M",
    "work_year": 2022,
    "remote_ratio": 100,
}

VALID_RESPONSE_BODY = {
    "prediction": 150000.0,
    "currency": "USD",
    "model_version": "2026-09-19.1",
    "inputs": VALID_INPUTS,
    "metadata": {"target": "salary_in_usd"},
}


def make_client(handler, **kwargs) -> SalaryApiClient:
    transport = httpx.MockTransport(handler)
    return SalaryApiClient(base_url="http://testserver", transport=transport, backoff_seconds=0.001, **kwargs)


def test_successful_prediction_parses_response():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=VALID_RESPONSE_BODY)

    client = make_client(handler)
    outcome = client.predict(VALID_INPUTS)

    assert outcome.success is True
    assert outcome.status_code == 200
    assert outcome.response_body["prediction"] == 150000.0


def test_422_is_not_retried():
    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        return httpx.Response(422, json={"error": {"code": "INVALID_INPUT", "message": "bad", "details": {}}})

    client = make_client(handler, max_retries=3)
    outcome = client.predict(VALID_INPUTS)

    assert outcome.success is False
    assert outcome.status_code == 422
    assert call_count["n"] == 1  # no retries for a deterministic client error


def test_500_is_retried_then_succeeds():
    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        if call_count["n"] < 3:
            return httpx.Response(503)
        return httpx.Response(200, json=VALID_RESPONSE_BODY)

    client = make_client(handler, max_retries=3)
    outcome = client.predict(VALID_INPUTS)

    assert outcome.success is True
    assert call_count["n"] == 3


def test_persistent_500_exhausts_retries_and_fails():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    client = make_client(handler, max_retries=2)
    outcome = client.predict(VALID_INPUTS)

    assert outcome.success is False
    assert outcome.status_code == 500
    assert "server error" in outcome.error


def test_connection_error_is_retried_then_fails():
    attempts = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["n"] += 1
        raise httpx.ConnectError("connection refused", request=request)

    client = make_client(handler, max_retries=2)
    outcome = client.predict(VALID_INPUTS)

    assert outcome.success is False
    assert attempts["n"] == 3  # initial attempt + 2 retries
    assert "ConnectError" in outcome.error


def test_timeout_is_retried_then_fails():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timed out", request=request)

    client = make_client(handler, max_retries=1)
    outcome = client.predict(VALID_INPUTS)

    assert outcome.success is False
    assert "Timeout" in outcome.error


def test_malformed_json_response_is_reported_as_failure():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"not json at all")

    client = make_client(handler)
    outcome = client.predict(VALID_INPUTS)

    assert outcome.success is False
    assert "malformed JSON" in outcome.error


def test_response_missing_required_fields_is_reported_as_failure():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"currency": "USD"})  # missing prediction/model_version

    client = make_client(handler)
    outcome = client.predict(VALID_INPUTS)

    assert outcome.success is False
    assert "missing fields" in outcome.error


def test_run_batch_continues_after_one_failure():
    def handler(request: httpx.Request) -> httpx.Response:
        params = dict(request.url.params)
        if params.get("experience_level") == "BAD":
            return httpx.Response(422, json={"error": {"code": "INVALID_INPUT", "message": "bad"}})
        return httpx.Response(200, json=VALID_RESPONSE_BODY)

    client = make_client(handler)
    rows = [VALID_INPUTS, {**VALID_INPUTS, "experience_level": "BAD"}, VALID_INPUTS]
    outcomes = run_batch(client, rows)

    assert len(outcomes) == 3
    assert [o.success for o in outcomes] == [True, False, True]


def test_run_batch_survives_predict_raising_unexpectedly(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=VALID_RESPONSE_BODY)

    client = make_client(handler)

    original_predict = client.predict
    calls = {"n": 0}

    def flaky_predict(inputs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("simulated bug")
        return original_predict(inputs)

    monkeypatch.setattr(client, "predict", flaky_predict)
    outcomes = run_batch(client, [VALID_INPUTS, VALID_INPUTS])

    assert len(outcomes) == 2
    assert outcomes[0].success is False
    assert "unexpected error" in outcomes[0].error
    assert outcomes[1].success is True
