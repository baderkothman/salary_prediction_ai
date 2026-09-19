"""Supabase persistence for pipeline runs and salary results.

Always uses the service-role key (backend/pipeline only -- security.md:
never the frontend). RLS on the live project (see supabase/migrations/)
already restricts anon reads to published runs and blocks all anon writes;
this client doesn't re-implement that, it just needs the service-role key
to bypass RLS as designed.

Publication strategy (architecture.md #8): a run starts 'building', results
are upserted under that run_id, and it only flips to 'published' once
decide_final_status() confirms enough of the attempted predictions actually
succeeded -- a run that fails that bar is marked 'failed' and is never
visible to the anon-key dashboard (the RLS policy filters on status).
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from supabase import Client, create_client

DEFAULT_MIN_SUCCESS_RATIO = 0.8


def compute_feature_signature(features: dict[str, Any]) -> str:
    """Deterministic id for a feature tuple, used as the upsert key so
    re-running the pipeline for the same run_id is idempotent."""
    canonical = json.dumps(features, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def decide_final_status(attempted: int, succeeded: int, min_success_ratio: float = DEFAULT_MIN_SUCCESS_RATIO) -> str:
    if attempted == 0:
        return "failed"
    return "published" if (succeeded / attempted) >= min_success_ratio else "failed"


class SupabasePersistence:
    def __init__(self, url: str, service_role_key: str, client: Client | None = None):
        self._client: Client = client or create_client(url, service_role_key)

    def start_run(
        self, model_version: str, dataset_hash: str, llm_model: str, prompt_version: str, model_metrics: dict
    ) -> str:
        response = (
            self._client.table("pipeline_runs")
            .insert(
                {
                    "status": "building",
                    "model_version": model_version,
                    "dataset_hash": dataset_hash,
                    "llm_model": llm_model,
                    "prompt_version": prompt_version,
                    "model_metrics": model_metrics,
                }
            )
            .execute()
        )
        return response.data[0]["id"]

    def upsert_result(
        self,
        run_id: str,
        features: dict[str, Any],
        predicted_salary_usd: float,
        analysis: dict[str, Any] | None = None,
        analysis_context: dict[str, Any] | None = None,
    ) -> None:
        row: dict[str, Any] = {
            "run_id": run_id,
            "feature_signature": compute_feature_signature(features),
            "work_year": features.get("work_year"),
            "experience_level": features["experience_level"],
            "employment_type": features["employment_type"],
            "job_title": features["job_title"],
            "employee_residence": features.get("employee_residence"),
            "remote_ratio": features.get("remote_ratio"),
            "company_location": features.get("company_location"),
            "company_size": features["company_size"],
            "features": features,
            "predicted_salary_usd": predicted_salary_usd,
        }
        if analysis is not None:
            row.update(
                {
                    "analysis_headline": analysis.get("headline"),
                    "analysis_summary": analysis.get("summary"),
                    "key_insights": analysis.get("insights"),
                    "chart_spec": analysis.get("chart"),
                    "limitations": analysis.get("limitations"),
                }
            )
        if analysis_context is not None:
            row["analysis_context"] = analysis_context

        self._client.table("salary_results").upsert(row, on_conflict="run_id,feature_signature").execute()

    def count_results(self, run_id: str) -> int:
        response = self._client.table("salary_results").select("id", count="exact").eq("run_id", run_id).execute()
        return response.count or 0

    def finalize_run(self, run_id: str, attempted: int, succeeded: int) -> str:
        status = decide_final_status(attempted, succeeded)
        update: dict[str, Any] = {"status": status}
        if status == "published":
            update["published_at"] = datetime.now(timezone.utc).isoformat()
        self._client.table("pipeline_runs").update(update).eq("id", run_id).execute()
        return status

    def get_latest_published_run(self) -> dict[str, Any] | None:
        response = (
            self._client.table("pipeline_runs")
            .select("*")
            .eq("status", "published")
            .order("published_at", desc=True)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None
