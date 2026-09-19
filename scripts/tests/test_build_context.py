import pandas as pd
import pytest

from scripts.build_context import build_analysis_context, find_comparison_group


def _dataset() -> pd.DataFrame:
    rows = []
    # 10 "Data Scientist" / SE rows (>= MIN_GROUP_SAMPLE_SIZE) so the specific group is used
    for salary in [100000, 110000, 120000, 130000, 140000, 150000, 160000, 170000, 180000, 190000]:
        rows.append({"experience_level": "SE", "job_title": "Data Scientist", "salary_in_usd": salary})
    # 3 "Rare Title" / MI rows (< MIN_GROUP_SAMPLE_SIZE), plus enough other MI rows to hit the fallback tier
    for salary in [60000, 65000, 70000]:
        rows.append({"experience_level": "MI", "job_title": "Rare Title", "salary_in_usd": salary})
    for salary in [80000, 85000, 90000, 95000, 100000, 105000, 110000, 115000]:
        rows.append({"experience_level": "MI", "job_title": "Other Title", "salary_in_usd": salary})
    return pd.DataFrame(rows)


def test_specific_group_used_when_sample_size_sufficient():
    df = _dataset()
    group, description = find_comparison_group(df, "SE", "Data Scientist")
    assert len(group) == 10
    assert "Data Scientist" in description


def test_falls_back_to_experience_level_when_specific_group_too_small():
    df = _dataset()
    group, description = find_comparison_group(df, "MI", "Rare Title")
    assert len(group) == 11  # all MI rows, not just the 3 "Rare Title" rows
    assert "Rare Title" not in description


def test_falls_back_to_full_dataset_when_nothing_meets_minimum():
    tiny_df = pd.DataFrame(
        [
            {"experience_level": "EX", "job_title": "CTO", "salary_in_usd": 300000},
            {"experience_level": "EN", "job_title": "Junior Analyst", "salary_in_usd": 50000},
        ]
    )
    group, description = find_comparison_group(tiny_df, "EX", "CTO")
    assert len(group) == 2
    assert description == "All roles in the dataset"


def test_build_analysis_context_shape():
    df = _dataset()
    context = build_analysis_context(df, {"experience_level": "SE", "job_title": "Data Scientist"}, 145000)

    assert context["prediction_usd"] == 145000.0
    assert context["comparison_group"]["sample_size"] == 10
    assert 0 <= context["percentile_rank_in_dataset"] <= 100
    assert isinstance(context["chart_data_by_experience_level"], list)
    assert all({"label", "value"} <= set(point.keys()) for point in context["chart_data_by_experience_level"])


def test_percentile_rank_is_deterministic_and_monotonic():
    df = _dataset()
    low = build_analysis_context(df, {"experience_level": "SE", "job_title": "Data Scientist"}, 50000)
    high = build_analysis_context(df, {"experience_level": "SE", "job_title": "Data Scientist"}, 500000)
    assert low["percentile_rank_in_dataset"] < high["percentile_rank_in_dataset"]
