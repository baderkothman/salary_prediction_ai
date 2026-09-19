import pandas as pd

from scripts.run_pipeline import select_narrative_sample


def _tuples(n_per_level: dict[str, int]) -> pd.DataFrame:
    rows = []
    for level, count in n_per_level.items():
        for i in range(count):
            rows.append({"experience_level": level, "job_title": f"Title {i}"})
    return pd.DataFrame(rows)


def test_returns_everything_when_pool_smaller_than_sample_size():
    tuples = _tuples({"EN": 3, "SE": 2})
    sample = select_narrative_sample(tuples, sample_size=20, seed=42)
    assert set(sample) == set(tuples.index)


def test_returns_exact_sample_size_when_pool_larger():
    tuples = _tuples({"EN": 81, "MI": 148, "SE": 118, "EX": 20})
    sample = select_narrative_sample(tuples, sample_size=20, seed=42)
    assert len(sample) == 20


def test_every_level_represented_at_least_once():
    tuples = _tuples({"EN": 81, "MI": 148, "SE": 118, "EX": 20})
    sample = select_narrative_sample(tuples, sample_size=20, seed=42)
    sampled_levels = set(tuples.loc[sample, "experience_level"])
    assert sampled_levels == {"EN", "MI", "SE", "EX"}


def test_deterministic_across_calls():
    tuples = _tuples({"EN": 81, "MI": 148, "SE": 118, "EX": 20})
    sample_a = select_narrative_sample(tuples, sample_size=20, seed=42)
    sample_b = select_narrative_sample(tuples, sample_size=20, seed=42)
    assert list(sample_a) == list(sample_b)


def test_different_seed_can_produce_different_sample():
    tuples = _tuples({"EN": 81, "MI": 148, "SE": 118, "EX": 20})
    sample_a = select_narrative_sample(tuples, sample_size=20, seed=42)
    sample_b = select_narrative_sample(tuples, sample_size=20, seed=1)
    assert set(sample_a) != set(sample_b)
