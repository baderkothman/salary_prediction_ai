import os

import pytest
from dotenv import load_dotenv

from scripts.persist import (
    SupabasePersistence,
    compute_feature_signature,
    decide_final_status,
)

load_dotenv(dotenv_path=".env")


def test_feature_signature_is_deterministic():
    features = {"experience_level": "SE", "job_title": "Data Scientist", "work_year": 2022}
    assert compute_feature_signature(features) == compute_feature_signature(dict(features))


def test_feature_signature_is_order_independent():
    a = {"experience_level": "SE", "job_title": "Data Scientist"}
    b = {"job_title": "Data Scientist", "experience_level": "SE"}
    assert compute_feature_signature(a) == compute_feature_signature(b)


def test_feature_signature_differs_for_different_features():
    a = {"experience_level": "SE", "job_title": "Data Scientist"}
    b = {"experience_level": "MI", "job_title": "Data Scientist"}
    assert compute_feature_signature(a) != compute_feature_signature(b)


@pytest.mark.parametrize(
    "attempted,succeeded,expected",
    [
        (0, 0, "failed"),
        (10, 10, "published"),
        (10, 8, "published"),  # exactly the 0.8 threshold
        (10, 7, "failed"),
        (100, 79, "failed"),
        (100, 80, "published"),
    ],
)
def test_decide_final_status_thresholds(attempted, succeeded, expected):
    assert decide_final_status(attempted, succeeded) == expected


REQUIRED_ENV_VARS = ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY")
HAS_SUPABASE_CREDS = all(os.environ.get(v) for v in REQUIRED_ENV_VARS)


@pytest.mark.skipif(not HAS_SUPABASE_CREDS, reason="SUPABASE_URL/SUPABASE_SERVICE_ROLE_KEY not set")
def test_full_persistence_round_trip_against_real_project():
    """Integration test against the real linked Supabase project: creates a
    throwaway run + result, exercises the full building -> published
    lifecycle, verifies get_latest_published_run picks it up, then cleans up.
    """
    persistence = SupabasePersistence(
        url=os.environ["SUPABASE_URL"], service_role_key=os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    )

    run_id = persistence.start_run(
        model_version="test-only",
        dataset_hash="test-hash",
        llm_model="test-model",
        prompt_version="v1",
        model_metrics={"mae": 1.0, "rmse": 1.0, "r2": 1.0},
    )

    try:
        features = {
            "experience_level": "SE",
            "employment_type": "FT",
            "job_title": "Data Scientist",
            "employee_residence": "US",
            "company_location": "US",
            "company_size": "M",
            "work_year": 2022,
            "remote_ratio": 100,
        }
        persistence.upsert_result(
            run_id=run_id,
            features=features,
            predicted_salary_usd=150000.0,
            analysis={"headline": "test", "summary": "test", "insights": [], "limitations": [], "chart": {}},
            analysis_context={"prediction_usd": 150000.0},
        )

        assert persistence.count_results(run_id) == 1

        # Idempotency: upserting the exact same feature tuple again should
        # not create a second row.
        persistence.upsert_result(run_id=run_id, features=features, predicted_salary_usd=150000.0)
        assert persistence.count_results(run_id) == 1

        status = persistence.finalize_run(run_id, attempted=1, succeeded=1)
        assert status == "published"

        latest = persistence.get_latest_published_run()
        assert latest is not None
        assert latest["id"] == run_id
    finally:
        persistence._client.table("pipeline_runs").delete().eq("id", run_id).execute()


@pytest.mark.skipif(not HAS_SUPABASE_CREDS, reason="SUPABASE_URL/SUPABASE_SERVICE_ROLE_KEY not set")
def test_failed_run_is_not_returned_as_latest_published():
    persistence = SupabasePersistence(
        url=os.environ["SUPABASE_URL"], service_role_key=os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    )
    run_id = persistence.start_run(
        model_version="test-only-failed",
        dataset_hash="test-hash",
        llm_model="test-model",
        prompt_version="v1",
        model_metrics={},
    )
    try:
        status = persistence.finalize_run(run_id, attempted=10, succeeded=1)
        assert status == "failed"

        latest = persistence.get_latest_published_run()
        assert latest is None or latest["id"] != run_id
    finally:
        persistence._client.table("pipeline_runs").delete().eq("id", run_id).execute()
