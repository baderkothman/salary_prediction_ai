"""Deterministic analysis-context builder.

architecture.md #3.7 / essentials.md #8: the LLM is a narrator, not a
calculator. Every number the LLM will see is computed here, in plain
pandas, before Ollama is ever called -- this module has zero LLM
dependency and is trivially testable on its own.
"""

import pandas as pd

MIN_GROUP_SAMPLE_SIZE = 8

EXPERIENCE_LABELS = {
    "EN": "entry-level",
    "MI": "mid-level",
    "SE": "senior-level",
    "EX": "executive-level",
}


def find_comparison_group(df: pd.DataFrame, experience_level: str, job_title: str) -> tuple[pd.DataFrame, str]:
    """Prefer the most specific group (job title + experience level) that
    still has enough rows to be meaningful; fall back to broader groups
    rather than reporting statistics from a handful of rows."""
    label = EXPERIENCE_LABELS.get(experience_level, experience_level)

    specific = df[(df["experience_level"] == experience_level) & (df["job_title"] == job_title)]
    if len(specific) >= MIN_GROUP_SAMPLE_SIZE:
        return specific, f"{job_title} roles at {label}"

    by_experience = df[df["experience_level"] == experience_level]
    if len(by_experience) >= MIN_GROUP_SAMPLE_SIZE:
        return by_experience, f"All roles at {label}"

    return df, "All roles in the dataset"


def compute_comparison_stats(group: pd.DataFrame, description: str) -> dict:
    salaries = group["salary_in_usd"]
    return {
        "description": description,
        "sample_size": len(group),
        "mean_salary_usd": round(float(salaries.mean()), 2),
        "median_salary_usd": round(float(salaries.median()), 2),
        "p25_salary_usd": round(float(salaries.quantile(0.25)), 2),
        "p75_salary_usd": round(float(salaries.quantile(0.75)), 2),
    }


def compute_percentile_rank(df: pd.DataFrame, predicted_salary: float) -> float:
    return round(float((df["salary_in_usd"] < predicted_salary).mean() * 100), 1)


def build_experience_level_chart_data(df: pd.DataFrame) -> list[dict]:
    order = ["EN", "MI", "SE", "EX"]
    medians = df.groupby("experience_level")["salary_in_usd"].median()
    return [
        {"label": EXPERIENCE_LABELS[level], "value": round(float(medians[level]), 2)}
        for level in order
        if level in medians.index
    ]


def build_analysis_context(df: pd.DataFrame, inputs: dict, predicted_salary: float) -> dict:
    group, description = find_comparison_group(df, inputs["experience_level"], inputs["job_title"])
    return {
        "prediction_usd": round(float(predicted_salary), 2),
        "inputs": inputs,
        "comparison_group": compute_comparison_stats(group, description),
        "percentile_rank_in_dataset": compute_percentile_rank(df, predicted_salary),
        "chart_data_by_experience_level": build_experience_level_chart_data(df),
    }
