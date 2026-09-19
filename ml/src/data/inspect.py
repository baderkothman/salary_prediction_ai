"""Dataset inspection for the raw Kaggle Data Science Job Salaries CSV.

Produces a machine-readable profile (ml/artifacts/reports/data_profile.json)
and a human-readable summary (docs/data_inspection.md) WITHOUT modifying or
writing back to the raw file. Run before any cleaning code is written.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

RAW_PATH = Path("ml/data/raw/ds_salaries.csv")
REPORT_JSON_PATH = Path("ml/artifacts/reports/data_profile.json")
REPORT_MD_PATH = Path("docs/data_inspection.md")

EXPECTED_EXPERIENCE_LEVELS = {"EN", "MI", "SE", "EX"}
EXPECTED_EMPLOYMENT_TYPES = {"FT", "PT", "CT", "FL"}
EXPECTED_COMPANY_SIZES = {"S", "M", "L"}
EXPECTED_REMOTE_RATIOS = {0, 50, 100}


def sha256_of_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iqr_outlier_bounds(series: pd.Series) -> tuple[float, float]:
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    return q1 - 1.5 * iqr, q3 + 1.5 * iqr


def profile_numeric(df: pd.DataFrame, column: str) -> dict:
    series = df[column]
    lower, upper = iqr_outlier_bounds(series)
    outliers = series[(series < lower) | (series > upper)]
    return {
        "min": float(series.min()),
        "max": float(series.max()),
        "mean": float(series.mean()),
        "median": float(series.median()),
        "std": float(series.std()),
        "p25": float(series.quantile(0.25)),
        "p75": float(series.quantile(0.75)),
        "iqr_outlier_bounds": [float(lower), float(upper)],
        "iqr_outlier_count": int(outliers.shape[0]),
    }


def profile_categorical(df: pd.DataFrame, column: str, top_n: int = 15) -> dict:
    counts = df[column].value_counts()
    return {
        "n_unique": int(df[column].nunique()),
        "top_values": counts.head(top_n).to_dict(),
    }


def main() -> None:
    if not RAW_PATH.exists():
        raise FileNotFoundError(
            f"Raw dataset not found at {RAW_PATH}. Place the Kaggle CSV there before running inspection."
        )

    df = pd.read_csv(RAW_PATH)

    columns_report = {}
    for col in df.columns:
        columns_report[col] = {
            "dtype": str(df[col].dtype),
            "null_count": int(df[col].isna().sum()),
            "null_pct": round(float(df[col].isna().mean() * 100), 3),
            "n_unique": int(df[col].nunique()),
        }

    full_row_duplicates = int(df.duplicated().sum())
    business_key_cols = [c for c in df.columns if c != "Unnamed: 0"]
    business_key_duplicates = int(df.duplicated(subset=business_key_cols).sum())

    numeric_cols = ["work_year", "salary", "salary_in_usd", "remote_ratio"]
    categorical_cols = [
        "experience_level",
        "employment_type",
        "job_title",
        "salary_currency",
        "employee_residence",
        "remote_ratio",
        "company_location",
        "company_size",
    ]

    invalid_values = {
        "non_positive_salary_in_usd": int((df["salary_in_usd"] <= 0).sum()),
        "non_positive_salary": int((df["salary"] <= 0).sum()),
        "unexpected_experience_level": sorted(
            set(df["experience_level"].unique()) - EXPECTED_EXPERIENCE_LEVELS
        ),
        "unexpected_employment_type": sorted(
            set(df["employment_type"].unique()) - EXPECTED_EMPLOYMENT_TYPES
        ),
        "unexpected_company_size": sorted(
            set(df["company_size"].unique()) - EXPECTED_COMPANY_SIZES
        ),
        "unexpected_remote_ratio": sorted(
            set(df["remote_ratio"].unique()) - EXPECTED_REMOTE_RATIOS
        ),
    }

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_file": str(RAW_PATH),
        "content_sha256": sha256_of_file(RAW_PATH),
        "row_count": int(df.shape[0]),
        "column_count": int(df.shape[1]),
        "columns": list(df.columns),
        "column_profile": columns_report,
        "full_row_duplicate_count": full_row_duplicates,
        "business_key_duplicate_count": business_key_duplicates,
        "numeric_profile": {c: profile_numeric(df, c) for c in numeric_cols},
        "categorical_profile": {c: profile_categorical(df, c) for c in categorical_cols},
        "invalid_values": invalid_values,
        "target_variable": "salary_in_usd",
        "leakage_candidates": ["salary", "salary_currency"],
        "redundant_columns": ["Unnamed: 0"],
        "high_cardinality_columns": [
            c
            for c in categorical_cols
            if df[c].nunique() > 20
        ],
    }

    REPORT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(report, indent=2))

    md_lines = [
        "# Dataset Inspection Report",
        "",
        f"Generated: {report['generated_at']}",
        "",
        f"- Source file: `{report['source_file']}`",
        f"- SHA-256: `{report['content_sha256']}`",
        f"- Rows: {report['row_count']}",
        f"- Columns: {report['column_count']}",
        "",
        "## Columns",
        "",
        "| Column | Dtype | Nulls | Null % | Unique |",
        "|---|---|---:|---:|---:|",
    ]
    for col, info in columns_report.items():
        md_lines.append(
            f"| {col} | {info['dtype']} | {info['null_count']} | {info['null_pct']}% | {info['n_unique']} |"
        )

    md_lines += [
        "",
        "## Duplicates",
        "",
        f"- Full-row duplicates: {full_row_duplicates}",
        f"- Duplicates ignoring `Unnamed: 0` index column: {business_key_duplicates}",
        "",
        "## Numeric profile",
        "",
        "| Column | Min | Max | Mean | Median | Std | IQR outliers |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for col, stats in report["numeric_profile"].items():
        md_lines.append(
            f"| {col} | {stats['min']:.0f} | {stats['max']:.0f} | {stats['mean']:.1f} | "
            f"{stats['median']:.0f} | {stats['std']:.1f} | {stats['iqr_outlier_count']} |"
        )

    md_lines += [
        "",
        "## Categorical cardinality",
        "",
        "| Column | Unique values |",
        "|---|---:|",
    ]
    for col, info in report["categorical_profile"].items():
        md_lines.append(f"| {col} | {info['n_unique']} |")

    md_lines += [
        "",
        "## Invalid value checks",
        "",
        f"- Non-positive `salary_in_usd`: {invalid_values['non_positive_salary_in_usd']}",
        f"- Non-positive `salary`: {invalid_values['non_positive_salary']}",
        f"- Unexpected `experience_level` values: {invalid_values['unexpected_experience_level'] or 'none'}",
        f"- Unexpected `employment_type` values: {invalid_values['unexpected_employment_type'] or 'none'}",
        f"- Unexpected `company_size` values: {invalid_values['unexpected_company_size'] or 'none'}",
        f"- Unexpected `remote_ratio` values: {invalid_values['unexpected_remote_ratio'] or 'none'}",
        "",
        "## Decision record",
        "",
        f"- Target: `{report['target_variable']}`",
        f"- Leakage candidates (excluded from features): {', '.join(report['leakage_candidates'])}",
        f"- Redundant columns (dropped): {', '.join(report['redundant_columns'])}",
        f"- High-cardinality columns (>20 unique values): {', '.join(report['high_cardinality_columns']) or 'none'}",
    ]

    REPORT_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD_PATH.write_text("\n".join(md_lines) + "\n")

    print(f"Wrote {REPORT_JSON_PATH}")
    print(f"Wrote {REPORT_MD_PATH}")


if __name__ == "__main__":
    main()
