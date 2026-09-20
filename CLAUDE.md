# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository state

Fully implemented and verified end-to-end: real dataset → trained model → validated FastAPI → local Ollama analysis → Supabase (RLS-verified live) → React dashboard, plus a Dockerfile for the independently deployed API. Read the six spec docs before making non-trivial changes (this is also `plan.md` §1's mandated order):

1. `prd.md` — product requirements, functional requirements (FR-01…FR-12), acceptance criteria.
2. `architecture.md` — system design, component responsibilities, API/DB contracts, architectural invariants.
3. `essentials.md` — condensed fast-start contract; defer to `architecture.md`/`prd.md` on conflicts.
4. `security.md` — trust boundaries, secret handling, RLS policy requirements.
5. `design.md` — UI direction, layout, tokens, component list for the React app.
6. `plan.md` — the phased execution plan this project followed.

## What this project is

An end-to-end ML salary-prediction system for data-science jobs (Kaggle `ruchi798/data-science-job-salaries`), split into two deliberately separate halves:

- **Local generation pipeline** (not deployed): cleans data, trains a `DecisionTreeRegressor` via scikit-learn `Pipeline`, calls a local FastAPI instance to get predictions for every distinct observed feature tuple, builds deterministic comparison statistics in Python, sends those facts to a **local Ollama** model to get a structured narrative + chart spec, validates that output, and publishes it to Supabase.
- **Deployed consumption layer**: a React/Vite/TypeScript dashboard that reads only from Supabase (published runs), plus an **independently deployed FastAPI** instance (Docker) serving the same model artifact for direct API evaluation.

Every page except one reads only Supabase at runtime. The one exception — `/predict` (`frontend/src/pages/PredictPage.tsx`) — was added later at the user's explicit request, overriding the invariant below; see Deviations.

## Architectural invariants (do not violate without documenting the change — `architecture.md` §12)

1. Production model is a `DecisionTreeRegressor` (not swapped for another algorithm in production).
2. Prediction API is **GET**-based with query params, not POST.
3. All API inputs are validated against model metadata (`ml/artifacts/model/model_metadata.json`), read at runtime — never hardcoded domain lists.
4. Preprocessing and the model are serialized together in one scikit-learn `Pipeline` so they can never drift apart.
5. Ollama runs locally only, used during pre-generation — never called live from the deployed dashboard.
6. Dashboard data is always persisted (to Supabase) before it is displayed.
7. React reads from Supabase only for every page except `/predict` (user-requested exception, see Deviations) — no other page generates analysis live or calls the FastAPI predict endpoint.
8. The deployed FastAPI service is an independent deliverable (own Dockerfile, own minimal `requirements.txt`, zero import dependency on `ml/`), functional even if the dashboard is down.
9. A `pipeline_runs` row starts as `building` and is only flipped to `published` after a completeness check (`scripts/persist.py::decide_final_status`, ≥80% prediction success ratio) — partial runs must never be exposed to the dashboard. RLS enforces this at the database level, not just in application code.
10. LLM output is untrusted structured data: validate with Pydantic before persistence (`scripts/llm_client.py`), validate again with Zod on the frontend before rendering (`frontend/src/lib/schemas.ts`); never execute LLM-generated code and never render narrative via `dangerouslySetInnerHTML`.

## Actual repository layout

```text
frontend/src/
  lib/        supabase.ts (browser client), api.ts (the one client hitting the backend, for /predict
              only), schemas.ts (Zod), queries.ts (TanStack Query hooks, server-side filtering/
              pagination), stats.ts, format.ts
  components/ AppHeader, PageContainer, MetricCard, FilterBar, ResultsTable, SalaryChart
              (allowlisted bar/horizontal_bar/line only), NarrativeSection, LimitationsCallout, ...
  pages/      OverviewPage, ExplorePage, ResultDetailPage, MethodologyPage, PredictPage (Supabase-only
              except this one -- see Deviations)
  test/setup.ts  jsdom + RTL cleanup (explicit afterEach, no vitest `globals: true`) + ResizeObserver polyfill for Recharts
backend/
  app/{core,schemas,services,api}/  config.py, errors.py (stable {error:{code,message,details}} shape),
                                     predictor.py (loads joblib+metadata, zero ml/ import),
                                     narrator.py (only /narrate; imports scripts/, provider-switchable),
                                     gemini_client.py (cloud narrator alternative, used when NARRATOR_PROVIDER=gemini),
                                     routes.py, dependencies.py
  requirements.txt   deployable set (includes httpx for narrator.py); Dockerfile builds from repo root
ml/
  data/{raw,processed}/, src/{data,features,training,evaluation}/, artifacts/{model,reports}/, tests/
scripts/    local generation pipeline: api_client.py, build_context.py, llm_client.py, persist.py, run_pipeline.py
supabase/migrations/   pipeline_runs, salary_results, RLS policies (anon SELECT on published only, no anon writes)
docs/       generated reports (data_inspection, cleaning is in ml/artifacts/reports) + decision records
            (feature_decision_record.md, ollama_model_choice.md)
```

Do not duplicate preprocessing logic across `ml/`, `scripts/`, and `backend/` — the serialized `Pipeline` artifact (`ml/artifacts/model/salary_model.joblib`) plus `model_metadata.json` are the single source of truth; `backend/` only deserializes them.

Small dataset/model artifacts (`ml/data/raw`, `ml/data/processed`, `ml/artifacts/`) are committed to git rather than ignored — the dataset is small (~600 rows) and committing the trained artifact lets the independently-deployed FastAPI service deploy without a training step in CI.

## Commands

```bash
# Python (one shared .venv for ml + backend + scripts)
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

python -m ml.src.data.inspect         # -> docs/data_inspection.md
python -m ml.src.data.clean           # -> ml/data/processed/salaries_clean.csv
python -m ml.src.training.train       # -> ml/artifacts/model/{salary_model.joblib,model_metadata.json}
uvicorn backend.app.main:app --reload --port 8000
python -m scripts.run_pipeline        # needs the API + Ollama both running
pytest                                 # 81 tests
ruff check .

# Frontend
cd frontend && npm install && npm run dev && npm run build && npm test   # 48 tests (vitest)

# Docker (backend, independent deployment) -- live at
# https://salary-prediction-api-65r0.onrender.com (Render free tier, render.yaml blueprint)
docker build -f backend/Dockerfile -t salary-prediction-api .   # from repo root
docker run -p 8000:8000 salary-prediction-api

# Supabase
supabase login --token <token> && supabase link --project-ref <ref> && supabase db push
```

## Non-obvious rules worth remembering

- **Input coverage, not Cartesian product**: `scripts/run_pipeline.py` predicts every *distinct observed* feature tuple (367 in the current dataset), not every possible combination. LLM narrative generation is separately capped to a fixed, stratified, seeded sample (20) — a local ~3B model takes 10–25s/call, so narrating everything would take over an hour. This only bounds the LLM step; prediction coverage is unaffected.
- **LLM is a narrator, not a calculator**: `scripts/build_context.py` computes all statistics in pandas first; Ollama only explains pre-computed facts. Verified live: `qwen3:4b` (a reasoning model, `think` disabled) just echoed the input back instead of analyzing it — `llama3.2:latest` is the working default. See `docs/ollama_model_choice.md`, including a disclosed known failure mode (schema-valid but logically-backwards comparison direction).
- **`categorical_domains` in model metadata come from the fitted encoder's `categories_`**, not recomputed from the dataframe — this is why some distinct observed tuples get a legitimate 422 from `/predict` (a category value that existed only in the 20%-test split the encoder never saw). Expected behavior, not a bug.
- **Secrets boundary**: `SUPABASE_SERVICE_ROLE_KEY` is pipeline/backend-only, never prefixed `VITE_`. Confirmed absent from `frontend/dist/` after build; the anon key is present there by design (RLS is what actually protects it).
- **Endpoint paths are flat** (`/health`, `/model/info`, `/predict`), not `/api/v1/...` as in `architecture.md`'s original example — a deliberate, documented, low-risk deviation following a later master prompt.
- **Error contracts**: FastAPI never returns raw stack traces; every error path (domain validation, FastAPI's own validation, HTTP errors, unexpected exceptions) returns the same `{"error": {"code", "message", "details"}}` shape.
- **Model artifact trust**: `joblib`/pickle can execute code on load — only load artifacts produced by this project's own trusted pipeline.
- **Frontend test setup**: `vitest.config.ts` does not set `test.globals: true` (every test file imports `describe/it/expect` explicitly), so `@testing-library/react`'s automatic cleanup never auto-registers — `src/test/setup.ts` wires `afterEach(cleanup)` explicitly. Omitting this causes DOM from prior tests to silently accumulate and produces "multiple elements found" failures that look unrelated to the real cause.
- **`pipeline_runs.model_metrics` is nested `{train: {...}, test: {...}}`**, not flat `{mae, rmse, r2}` — it's stored exactly as `train.py` writes `model_metadata.json`'s `metrics` field. A real bug shipped here once: the frontend Zod schema and its test fixtures both assumed the flat shape, agreeing with each other while disagreeing with the real data, so no test caught it — only opening the actual running app did. `frontend/src/lib/schemas.test.ts` now has a regression test built from a real Supabase row.
- **`/narrate` needs the cleaned dataset (`ml/data/processed/salaries_clean.csv`) and a reachable Ollama** in addition to the model artifact `/predict` needs — a deployment that omits either still boots and serves `/predict`/`/health`/`/model/info`, but `/narrate` returns a 503 (`NARRATOR_UNAVAILABLE`). Distinguish `OLLAMA_UNAVAILABLE` (unreachable) from `NARRATIVE_GENERATION_FAILED` (reachable, never returned valid JSON after retries) when debugging.

## Deviations from the original spec docs (documented, not silent)

- **Live "Prediction page" (`/predict`) exists**, calling the backend directly from the browser. This was initially built and then deliberately *omitted* because it contradicts `architecture.md` invariant #7 and `prd.md`'s non-goal ("React-to-FastAPI prediction requests as part of the dashboard flow") — but the user then explicitly asked for exactly this feature, which is a legitimate override of that call: the user is the final authority on product scope, not the spec docs. Implemented as narrowly as possible:
  - New backend `GET /narrate` endpoint (`backend/app/services/narrator.py`) — the *only* thing in `backend/` that imports from `scripts/` (`build_context.py`, and `llm_client.py` when `NARRATOR_PROVIDER=ollama`). `/health`, `/model/info`, `/predict` are untouched and still fully independent per invariant #8; `/narrate` degrades to a clean 503 rather than failing app startup if the dataset or provider isn't reachable.
  - **`NARRATOR_PROVIDER` switches the narrator between `ollama` (default, local dev) and `gemini`** (`backend/app/services/gemini_client.py`) — added because a deployed backend (Render) can't reach a developer's local Ollama instance. This is a second explicit user override: prd.md's original goal was local-LLM-only with no external provider, but that goal was scoped to the offline generation pipeline; `scripts/llm_client.py` (used by `scripts/run_pipeline.py`) is unconditionally still Ollama-only regardless of this setting — only the live, on-demand `/narrate` path swaps providers. Both clients implement the same `generate_salary_analysis(context) -> (SalaryAnalysis | None, error)` shape and share the same Pydantic schema/system prompt from `scripts/llm_client.py`, so `NarratorService.narrate()` doesn't care which one is active. Gemini's `thinkingConfig.thinkingBudget=0` is set deliberately — confirmed live that it cuts token usage ~7x with no quality loss for this constrained JSON task.
  - Every other page is still Supabase-only. This is a single, contained, documented exception — not a reversal of the architecture.
- **Directory layout** (`frontend/`/`backend/`/`ml/`/`scripts/`) supersedes `architecture.md` §4's `apps/`/`pipeline/` naming, again per a later master prompt with no strong technical reason to refuse it.
