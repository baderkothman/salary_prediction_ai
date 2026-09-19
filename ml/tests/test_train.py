import json

import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.pipeline import Pipeline

from ml.src.features.build_features import FEATURE_COLUMNS
from ml.src.training.train import (
    METADATA_PATH,
    MODEL_PATH,
    build_pipeline,
    extract_categorical_domains,
)


def _toy_dataset(n: int = 40) -> pd.DataFrame:
    rng = np.random.default_rng(0)
    experience = rng.choice(["EN", "MI", "SE", "EX"], size=n)
    base = {"EN": 60000, "MI": 90000, "SE": 130000, "EX": 170000}
    salary = np.array([base[e] for e in experience]) + rng.integers(-5000, 5000, size=n)
    return pd.DataFrame(
        {
            "experience_level": experience,
            "employment_type": rng.choice(["FT", "PT"], size=n),
            "job_title": rng.choice(["Data Scientist", "Data Engineer"], size=n),
            "employee_residence": rng.choice(["US", "DE"], size=n),
            "company_location": rng.choice(["US", "DE"], size=n),
            "company_size": rng.choice(["S", "M", "L"], size=n),
            "work_year": rng.choice([2020, 2021, 2022], size=n),
            "remote_ratio": rng.choice([0, 50, 100], size=n),
            "salary_in_usd": salary,
        }
    )


def test_pipeline_trains_and_predicts_finite_non_negative_values():
    df = _toy_dataset()
    pipeline = build_pipeline()
    pipeline.fit(df[FEATURE_COLUMNS], df["salary_in_usd"])
    preds = pipeline.predict(df[FEATURE_COLUMNS])
    assert np.all(np.isfinite(preds))
    assert np.all(preds >= 0)


def test_unseen_category_does_not_crash_prediction():
    df = _toy_dataset()
    pipeline = build_pipeline()
    pipeline.fit(df[FEATURE_COLUMNS], df["salary_in_usd"])

    unseen_row = df[FEATURE_COLUMNS].iloc[[0]].copy()
    unseen_row["job_title"] = "Some Brand New Title Never Seen In Training"
    pred = pipeline.predict(unseen_row)
    assert np.isfinite(pred[0])


def test_extract_categorical_domains_matches_fitted_encoder():
    df = _toy_dataset()
    pipeline = build_pipeline()
    pipeline.fit(df[FEATURE_COLUMNS], df["salary_in_usd"])
    domains = extract_categorical_domains(pipeline)
    assert set(domains["experience_level"]) == set(df["experience_level"].unique())


@pytest.mark.skipif(not MODEL_PATH.exists(), reason="trained artifact not present in this environment")
def test_saved_artifact_loads_and_predicts_in_a_fresh_process():
    loaded: Pipeline = joblib.load(MODEL_PATH)
    metadata = json.loads(METADATA_PATH.read_text())

    sample_input = pd.DataFrame(
        [
            {
                "experience_level": metadata["categorical_domains"]["experience_level"][0],
                "employment_type": metadata["categorical_domains"]["employment_type"][0],
                "job_title": metadata["categorical_domains"]["job_title"][0],
                "employee_residence": metadata["categorical_domains"]["employee_residence"][0],
                "company_location": metadata["categorical_domains"]["company_location"][0],
                "company_size": metadata["categorical_domains"]["company_size"][0],
                "work_year": metadata["numeric_ranges"]["work_year"]["max"],
                "remote_ratio": metadata["numeric_ranges"]["remote_ratio"]["allowed_values"][0],
            }
        ]
    )
    prediction = loaded.predict(sample_input)
    assert prediction.shape == (1,)
    assert np.isfinite(prediction[0])
    assert prediction[0] >= 0


@pytest.mark.skipif(not METADATA_PATH.exists(), reason="metadata not present in this environment")
def test_metadata_has_required_fields():
    metadata = json.loads(METADATA_PATH.read_text())
    for key in ("model_name", "model_version", "target", "feature_columns", "metrics", "dataset_hash"):
        assert key in metadata
    assert "mae" in metadata["metrics"]["test"]
    assert "rmse" in metadata["metrics"]["test"]
    assert "r2" in metadata["metrics"]["test"]
