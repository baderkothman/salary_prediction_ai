"""End-to-end local generation pipeline orchestration.

cleaned data -> distinct observed feature tuples -> FastAPI predictions
-> (sampled) Ollama narratives -> Supabase (building -> published/failed)

Narrative sampling policy: predicting via FastAPI is near-instant, so every
distinct observed tuple gets a real prediction call (FR-07's full observed-
space coverage is NOT reduced). Narrating via a local ~3B Ollama model takes
roughly 10-25s per call though, so narrating all ~367 observed tuples in
this dataset would take over an hour. NARRATIVE_SAMPLE_SIZE bounds that to a
fixed, reproducible (seeded), stratified-by-experience-level sample instead
-- this is a documented sampling policy for the LLM-analysis step
specifically, recorded in the coverage report written alongside the run.
"""

import json
import logging
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from ml.src.features.build_features import FEATURE_COLUMNS
from scripts.api_client import SalaryApiClient
from scripts.build_context import build_analysis_context
from scripts.llm_client import PROMPT_VERSION, OllamaClient, OllamaUnavailableError
from scripts.persist import SupabasePersistence

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("run_pipeline")

PROCESSED_PATH = Path("ml/data/processed/salaries_clean.csv")
MODEL_METADATA_PATH = Path("ml/artifacts/model/model_metadata.json")
RUN_REPORT_PATH = Path("ml/artifacts/reports/pipeline_run_report.json")

NARRATIVE_SAMPLE_SIZE = 20
NARRATIVE_SAMPLE_SEED = 42


def load_cleaned_data_and_tuples() -> tuple[pd.DataFrame, pd.DataFrame]:
    if not PROCESSED_PATH.exists():
        raise FileNotFoundError(f"{PROCESSED_PATH} not found; run `python -m ml.src.data.clean` first.")
    df = pd.read_csv(PROCESSED_PATH)
    tuples = df[FEATURE_COLUMNS].drop_duplicates().sort_values(FEATURE_COLUMNS).reset_index(drop=True)
    return df, tuples


def select_narrative_sample(tuples: pd.DataFrame, sample_size: int, seed: int) -> pd.Index:
    """Stratified by experience_level, proportional allocation, every level
    represented at least once, fixed seed for reproducibility."""
    if len(tuples) <= sample_size:
        return tuples.index

    levels = sorted(tuples["experience_level"].unique())
    target = {
        level: max(1, round(sample_size * (tuples["experience_level"] == level).sum() / len(tuples)))
        for level in levels
    }
    # Rounding rarely lands exactly on sample_size; absorb the remainder into the largest group.
    largest = max(target, key=target.get)
    target[largest] += sample_size - sum(target.values())

    picked_frames = []
    for level, n in target.items():
        group = tuples[tuples["experience_level"] == level]
        picked_frames.append(group.sample(n=min(max(n, 0), len(group)), random_state=seed))

    return pd.concat(picked_frames).index


def run_pipeline(
    api_base_url: str,
    supabase_url: str,
    supabase_service_role_key: str,
    ollama_base_url: str,
    ollama_model: str,
    narrative_sample_size: int = NARRATIVE_SAMPLE_SIZE,
) -> dict:
    df, tuples = load_cleaned_data_and_tuples()
    model_metadata = json.loads(MODEL_METADATA_PATH.read_text())

    persistence = SupabasePersistence(url=supabase_url, service_role_key=supabase_service_role_key)
    api_client = SalaryApiClient(base_url=api_base_url)
    llm_client = OllamaClient(base_url=ollama_base_url, model=ollama_model)

    run_id = persistence.start_run(
        model_version=model_metadata["model_version"],
        dataset_hash=model_metadata["dataset_hash"],
        llm_model=ollama_model,
        prompt_version=PROMPT_VERSION,
        model_metrics=model_metadata["metrics"],
    )
    logger.info("Started run %s (%d distinct observed feature tuples)", run_id, len(tuples))

    narrative_sample_idx = set(select_narrative_sample(tuples, narrative_sample_size, NARRATIVE_SAMPLE_SEED))

    prediction_success = 0
    prediction_failed = 0
    narrative_success = 0
    narrative_failed = 0
    narrative_skipped_ollama_unavailable = 0

    for idx, row in tuples.iterrows():
        inputs = {
            **row.to_dict(),
            "work_year": int(row["work_year"]),
            "remote_ratio": int(row["remote_ratio"]),
        }

        outcome = api_client.predict(inputs)
        if not outcome.success:
            prediction_failed += 1
            logger.warning("Prediction failed for %s: %s", inputs, outcome.error)
            continue

        prediction_success += 1
        predicted_salary = outcome.response_body["prediction"]

        analysis = None
        analysis_context = None
        if idx in narrative_sample_idx:
            analysis_context = build_analysis_context(df, inputs, predicted_salary)
            try:
                analysis_obj, error = llm_client.generate_salary_analysis(analysis_context)
            except OllamaUnavailableError as exc:
                narrative_skipped_ollama_unavailable += 1
                logger.warning("Ollama unavailable, skipping narrative for %s: %s", inputs, exc)
                analysis_obj, error = None, None

            if analysis_obj is not None:
                narrative_success += 1
                analysis = analysis_obj.model_dump()
            elif error is not None:
                narrative_failed += 1
                logger.warning("Narrative generation failed for %s: %s", inputs, error)

        persistence.upsert_result(
            run_id=run_id,
            features=inputs,
            predicted_salary_usd=predicted_salary,
            analysis=analysis,
            analysis_context=analysis_context,
        )

    final_status = persistence.finalize_run(run_id, attempted=len(tuples), succeeded=prediction_success)

    summary = {
        "run_id": run_id,
        "model_version": model_metadata["model_version"],
        "attempted_tuples": len(tuples),
        "prediction_success": prediction_success,
        "prediction_failed": prediction_failed,
        "narrative_sample_size": len(narrative_sample_idx),
        "narrative_success": narrative_success,
        "narrative_failed": narrative_failed,
        "narrative_skipped_ollama_unavailable": narrative_skipped_ollama_unavailable,
        "status": final_status,
    }
    RUN_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RUN_REPORT_PATH.write_text(json.dumps(summary, indent=2))
    logger.info("Pipeline run complete: %s", json.dumps(summary, indent=2))
    return summary


def main() -> None:
    load_dotenv(dotenv_path=".env")
    run_pipeline(
        api_base_url=os.environ.get("LOCAL_API_BASE_URL", "http://127.0.0.1:8000"),
        supabase_url=os.environ["SUPABASE_URL"],
        supabase_service_role_key=os.environ["SUPABASE_SERVICE_ROLE_KEY"],
        ollama_base_url=os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        ollama_model=os.environ.get("OLLAMA_MODEL", "llama3.2:latest"),
    )


if __name__ == "__main__":
    main()
