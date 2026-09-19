"""Train the Decision Tree salary regressor.

Correctness guardrails (see docs/feature_decision_record.md and prd.md FR-04):
- A single 80/20 train/test split is made ONCE; the test set is touched
  exactly once, for final evaluation.
- Hyperparameters are chosen via 5-fold cross-validation on the TRAINING
  split only (GridSearchCV), never against the held-out test set, so we are
  not "choosing hyperparameters using the final test set repeatedly."
- Preprocessing lives inside the Pipeline that GridSearchCV cross-validates,
  so each CV fold fits its own OneHotEncoder on that fold's training rows
  only -- this is what actually prevents preprocessing leakage across folds,
  not just the outer train/test split.
- categorical_domains in the metadata are read back from the FITTED
  encoder's `categories_`, not recomputed from the dataframe, so the API's
  validation domain can never drift from what the model actually supports.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeRegressor

from ml.src.data.hashing import sha256_of_file
from ml.src.evaluation.evaluate import compute_regression_metrics
from ml.src.features.build_features import (
    CATEGORICAL_FEATURES,
    FEATURE_COLUMNS,
    NUMERIC_FEATURES,
    build_preprocessor,
)

PROCESSED_PATH = Path("ml/data/processed/salaries_clean.csv")
MODEL_PATH = Path("ml/artifacts/model/salary_model.joblib")
METADATA_PATH = Path("ml/artifacts/model/model_metadata.json")

TARGET_COLUMN = "salary_in_usd"
RANDOM_STATE = 42
TEST_SIZE = 0.2
CV_FOLDS = 5

PARAM_GRID = {
    "model__max_depth": [3, 5, 8, 12, None],
    "model__min_samples_split": [2, 10, 20],
    "model__min_samples_leaf": [1, 5, 10],
}


def build_pipeline() -> Pipeline:
    return Pipeline(
        steps=[
            ("preprocessor", build_preprocessor()),
            ("model", DecisionTreeRegressor(random_state=RANDOM_STATE)),
        ]
    )


def load_dataset() -> pd.DataFrame:
    if not PROCESSED_PATH.exists():
        raise FileNotFoundError(
            f"Processed dataset not found at {PROCESSED_PATH}; run `python -m ml.src.data.clean` first."
        )
    return pd.read_csv(PROCESSED_PATH)


def extract_categorical_domains(fitted_pipeline: Pipeline) -> dict:
    encoder = fitted_pipeline.named_steps["preprocessor"].named_transformers_["categorical"]
    return {
        col: sorted(cats.tolist())
        for col, cats in zip(CATEGORICAL_FEATURES, encoder.categories_, strict=True)
    }


def main() -> None:
    df = load_dataset()
    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )

    search = GridSearchCV(
        estimator=build_pipeline(),
        param_grid=PARAM_GRID,
        cv=CV_FOLDS,
        scoring="neg_mean_absolute_error",
        n_jobs=-1,
    )
    search.fit(X_train, y_train)
    best_pipeline: Pipeline = search.best_estimator_

    train_metrics = compute_regression_metrics(y_train, best_pipeline.predict(X_train))
    test_metrics = compute_regression_metrics(y_test, best_pipeline.predict(X_test))

    model_version = datetime.now(timezone.utc).strftime("%Y-%m-%d") + ".1"

    metadata = {
        "model_name": "decision_tree_salary_regressor",
        "model_version": model_version,
        "target": TARGET_COLUMN,
        "feature_columns": FEATURE_COLUMNS,
        "categorical_features": CATEGORICAL_FEATURES,
        "numeric_features": NUMERIC_FEATURES,
        "categorical_domains": extract_categorical_domains(best_pipeline),
        "numeric_ranges": {
            "work_year": {"min": int(df["work_year"].min()), "max": int(df["work_year"].max())},
            "remote_ratio": {
                "min": int(df["remote_ratio"].min()),
                "max": int(df["remote_ratio"].max()),
                "allowed_values": sorted(int(v) for v in df["remote_ratio"].unique()),
            },
        },
        "hyperparameters": search.best_params_,
        "cross_validation": {
            "folds": CV_FOLDS,
            "scoring": "neg_mean_absolute_error",
            "best_cv_score_mae": float(-search.best_score_),
        },
        "metrics": {"train": train_metrics, "test": test_metrics},
        "random_state": RANDOM_STATE,
        "dataset_hash": sha256_of_file(PROCESSED_PATH),
        "dataset_row_count": len(df),
        "train_row_count": len(X_train),
        "test_row_count": len(X_test),
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_pipeline, MODEL_PATH)
    METADATA_PATH.write_text(json.dumps(metadata, indent=2))

    print(f"Best params: {search.best_params_}")
    print(f"Train metrics: {train_metrics}")
    print(f"Test metrics:  {test_metrics}")
    print(f"Wrote {MODEL_PATH}")
    print(f"Wrote {METADATA_PATH}")


if __name__ == "__main__":
    main()
