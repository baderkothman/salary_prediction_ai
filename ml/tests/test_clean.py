from pathlib import Path

import pandas as pd
import pytest

from ml.src.data.clean import RAW_PATH, SchemaError, clean_dataframe

VALID_ROW = {
    "work_year": 2022,
    "experience_level": "SE",
    "employment_type": "FT",
    "job_title": "Data Scientist",
    "salary": 100000,
    "salary_currency": "USD",
    "salary_in_usd": 100000,
    "employee_residence": "US",
    "remote_ratio": 100,
    "company_location": "US",
    "company_size": "M",
}


def make_df(rows: list[dict], with_index_column: bool = True) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    if with_index_column:
        df.insert(0, "Unnamed: 0", range(len(df)))
    return df


def test_cleaning_is_deterministic():
    df_raw = make_df([VALID_ROW, {**VALID_ROW, "job_title": "ML Engineer"}])
    cleaned_a, report_a = clean_dataframe(df_raw.copy())
    cleaned_b, report_b = clean_dataframe(df_raw.copy())
    pd.testing.assert_frame_equal(cleaned_a, cleaned_b)
    assert report_a == report_b


def test_drops_redundant_index_and_leakage_columns():
    df_raw = make_df([VALID_ROW])
    cleaned, report = clean_dataframe(df_raw)
    assert "Unnamed: 0" not in cleaned.columns
    assert "salary" not in cleaned.columns
    assert "salary_currency" not in cleaned.columns
    assert report["columns_dropped_redundant"] == ["Unnamed: 0"]
    assert report["columns_dropped_leakage"] == ["salary", "salary_currency"]


def test_removes_duplicate_rows_created_by_index_column():
    # Two rows that are true duplicates of each other, disguised as unique
    # only by the meaningless "Unnamed: 0" index column.
    df_raw = make_df([VALID_ROW, VALID_ROW])
    cleaned, report = clean_dataframe(df_raw)
    assert report["duplicate_rows_removed"] == 1
    assert len(cleaned) == 1


def test_missing_target_column_raises_schema_error():
    df_raw = make_df([VALID_ROW]).drop(columns=["salary_in_usd"])
    with pytest.raises(SchemaError):
        clean_dataframe(df_raw)


def test_unexpected_missing_values_raise_schema_error():
    df_raw = make_df([VALID_ROW, VALID_ROW])
    df_raw.loc[1, "job_title"] = None
    with pytest.raises(SchemaError):
        clean_dataframe(df_raw)


def test_unexpected_categorical_value_raises_schema_error():
    df_raw = make_df([{**VALID_ROW, "experience_level": "NOT_A_LEVEL"}])
    with pytest.raises(SchemaError):
        clean_dataframe(df_raw)


def test_non_positive_target_raises_schema_error():
    df_raw = make_df([{**VALID_ROW, "salary_in_usd": 0}])
    with pytest.raises(SchemaError):
        clean_dataframe(df_raw)


@pytest.mark.skipif(not RAW_PATH.exists(), reason="raw dataset not present in this environment")
def test_real_dataset_cleans_as_expected():
    df_raw = pd.read_csv(RAW_PATH)
    cleaned, report = clean_dataframe(df_raw)
    assert report["input_row_count"] == 607
    assert report["duplicate_rows_removed"] == 42
    assert report["output_row_count"] == 565
    assert cleaned.isna().sum().sum() == 0
    assert "salary" not in cleaned.columns
    assert "salary_currency" not in cleaned.columns
