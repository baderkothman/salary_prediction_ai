"""Reproducible cleaning pipeline for the raw salary dataset.

`clean_dataframe` is a pure function (no filesystem access) so it can be
tested deterministically. `main()` wires it to the real raw/processed paths
and writes the cleaning report required by prd.md FR-02.

Decisions here follow docs/feature_decision_record.md:
- Fail fast (raise SchemaError) on missing target, missing values, or
  unexpected category codes rather than silently coercing/dropping.
- Duplicates are only meaningful after the redundant index column is
  dropped, so column drop must happen before the duplicate check.
- Leakage columns (salary, salary_currency) are removed at the cleaning
  stage, not left for later stages to remember to exclude.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from ml.src.data.hashing import sha256_of_file

RAW_PATH = Path("ml/data/raw/ds_salaries.csv")
PROCESSED_PATH = Path("ml/data/processed/salaries_clean.csv")
REPORT_PATH = Path("ml/artifacts/reports/cleaning_report.json")

TARGET_COLUMN = "salary_in_usd"
REQUIRED_COLUMNS = [
    "work_year",
    "experience_level",
    "employment_type",
    "job_title",
    "salary",
    "salary_currency",
    "salary_in_usd",
    "employee_residence",
    "remote_ratio",
    "company_location",
    "company_size",
]
REDUNDANT_COLUMNS = ["Unnamed: 0"]
LEAKAGE_COLUMNS = ["salary", "salary_currency"]

EXPECTED_EXPERIENCE_LEVELS = {"EN", "MI", "SE", "EX"}
EXPECTED_EMPLOYMENT_TYPES = {"FT", "PT", "CT", "FL"}
EXPECTED_COMPANY_SIZES = {"S", "M", "L"}
EXPECTED_REMOTE_RATIOS = {0, 50, 100}


class SchemaError(ValueError):
    """Raised when the input data does not match the contract this pipeline was built for."""


def validate_schema(df: pd.DataFrame) -> None:
    missing_required = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_required:
        raise SchemaError(f"Missing required columns: {sorted(missing_required)}")


def clean_dataframe(df_raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    validate_schema(df_raw)
    df = df_raw.copy()
    input_row_count = len(df)

    columns_dropped_redundant = [c for c in REDUNDANT_COLUMNS if c in df.columns]
    df = df.drop(columns=columns_dropped_redundant)

    null_counts = df.isna().sum()
    total_nulls = int(null_counts.sum())
    if total_nulls > 0:
        raise SchemaError(
            "Unexpected missing values found and no imputation strategy is defined "
            f"for this schema: {null_counts[null_counts > 0].to_dict()}"
        )

    duplicate_mask = df.duplicated(keep="first")
    duplicate_rows_removed = int(duplicate_mask.sum())
    df = df[~duplicate_mask].copy()

    invalid_categories = {
        "experience_level": set(df["experience_level"].unique()) - EXPECTED_EXPERIENCE_LEVELS,
        "employment_type": set(df["employment_type"].unique()) - EXPECTED_EMPLOYMENT_TYPES,
        "company_size": set(df["company_size"].unique()) - EXPECTED_COMPANY_SIZES,
        "remote_ratio": set(df["remote_ratio"].unique()) - EXPECTED_REMOTE_RATIOS,
    }
    bad_categories = {k: sorted(v) for k, v in invalid_categories.items() if v}
    if bad_categories:
        raise SchemaError(f"Unexpected categorical values found: {bad_categories}")

    if (df[TARGET_COLUMN] <= 0).any():
        raise SchemaError(f"Found non-positive {TARGET_COLUMN} values, which are impossible.")

    columns_dropped_leakage = [c for c in LEAKAGE_COLUMNS if c in df.columns]
    df = df.drop(columns=columns_dropped_leakage)

    df = df.sort_values(by=list(df.columns), kind="mergesort").reset_index(drop=True)

    report = {
        "input_row_count": input_row_count,
        "output_row_count": len(df),
        "duplicate_rows_removed": duplicate_rows_removed,
        "columns_dropped_redundant": columns_dropped_redundant,
        "columns_dropped_leakage": columns_dropped_leakage,
        "missing_values_before_cleaning": {k: int(v) for k, v in null_counts.items()},
        "target_column": TARGET_COLUMN,
        "final_feature_columns": [c for c in df.columns if c != TARGET_COLUMN],
    }
    return df, report


def main() -> None:
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"Raw dataset not found at {RAW_PATH}.")

    df_raw = pd.read_csv(RAW_PATH)
    df_clean, report = clean_dataframe(df_raw)

    report["generated_at"] = datetime.now(timezone.utc).isoformat()
    report["source_file"] = str(RAW_PATH)
    report["source_content_sha256"] = sha256_of_file(RAW_PATH)

    PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(PROCESSED_PATH, index=False)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2))

    print(f"Cleaned {report['input_row_count']} -> {report['output_row_count']} rows")
    print(f"Wrote {PROCESSED_PATH}")
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
