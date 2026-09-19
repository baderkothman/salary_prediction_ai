# Salary Prediction Application - Essentials

This file is the fast-start contract for an implementation agent. Read it before writing code, then read the other documents for details.

## 1. Build This

Create an end-to-end salary prediction project with:

- Python data cleaning.
- scikit-learn Decision Tree regression.
- FastAPI GET prediction API.
- Python script/client that calls the API robustly.
- Local Ollama analysis.
- Supabase persistence.
- React + Vite + TypeScript dashboard.
- Standalone deployed FastAPI service using the same trained model.

The original dashboard requirement was Streamlit. For this project, **React replaces Streamlit**.

---

## 2. Non-Negotiable Architecture

```text
LOCAL GENERATION
Dataset -> Clean -> Train -> Model
                    |
Distinct observed inputs -> Python client -> local FastAPI -> predictions
                                                     |
                                      stats/context -> Ollama
                                                     |
                                      validated narrative/chart
                                                     |
                                                  Supabase
                                                     |
DEPLOYED CONSUMPTION                               React
```

Separately:

```text
Same model artifact -> deployed FastAPI URL
```

The React dashboard should query Supabase directly under safe read-only RLS policies. It should not need Ollama or FastAPI to display its persisted dashboard results.

---

## 3. Tech Stack

### ML / pipeline

- Python 3.11+
- pandas
- numpy
- scikit-learn
- joblib
- pydantic
- httpx
- Ollama local API
- Supabase Python client or direct PostgREST client
- pytest

### API

- FastAPI
- Uvicorn
- Pydantic
- joblib
- pytest + HTTPX/TestClient

### Web

- React
- Vite
- TypeScript
- React Router
- TanStack Query
- `@supabase/supabase-js`
- Recharts
- Zod
- Tailwind CSS or an equivalent token-based styling layer
- Vitest
- React Testing Library

---

## 4. Dataset Rules

- Keep raw data immutable.
- Default target is `salary_in_usd`.
- Inspect the actual CSV before finalizing feature columns.
- Exclude target-leaking salary fields from input features.
- Derive categorical domains from data/model metadata.
- Use a reproducible random seed.
- Save a cleaning report and model evaluation report.

---

## 5. Model Rules

Required model:

```python
DecisionTreeRegressor
```

Use a scikit-learn `Pipeline` so preprocessing is serialized with the estimator.

Required evaluation:

- MAE
- RMSE
- R²

Persist:

```text
artifacts/model/salary_model.joblib
artifacts/model/model_metadata.json
```

---

## 6. API Rules

Required routes:

```text
GET /health
GET /api/v1/metadata
GET /api/v1/predict
```

`/api/v1/predict` must:

- Use query parameters.
- Validate required fields.
- Validate values/ranges.
- Return controlled 4xx responses for bad input.
- Never leak a stack trace.
- Include the model version in successful responses.

Load the model once during app startup.

---

## 7. Batch Prediction Rules

The pipeline must not blindly generate the full Cartesian product of every category.

Preferred coverage:

```text
cleaned model feature columns
-> drop_duplicates()
-> deterministic ordering
-> one API call per unique observed tuple
```

Create a coverage report with:

- total unique observed tuples
- attempted
- successful
- failed
- failure reasons
- category coverage per feature

No single failed request may crash the full batch.

---

## 8. LLM Rules

Use Ollama locally.

The LLM is a **narrator**, not the calculator.

Python computes all statistics first. The LLM receives those facts and turns them into a narrative plus a constrained chart choice.

The LLM response must be structured and validated before storage.

Minimum fields:

```text
headline
summary
key_insights[]
chart
limitations[]
```

Never execute LLM-generated code.

---

## 9. Supabase Rules

Use migrations.

Required logical tables:

- `pipeline_runs`
- `salary_results`

A run starts as `building` and becomes `published` only when generation is sufficiently complete.

The React application must only read `published` data.

Frontend uses only the public Supabase URL + anon key. Service-role credentials are backend/pipeline only.

---

## 10. React Requirements

Core dashboard sections:

```text
Overview
├── KPI cards
├── salary landscape chart
└── recent/model metadata

Explore
├── filters
├── charts
└── paginated results table

Result Detail
├── model inputs
├── predicted salary
├── LLM narrative
├── supporting statistics
└── generated chart

Methodology
├── dataset
├── model
├── metrics
├── limitations
└── generation timestamp/version
```

Required states:

- Loading
- Empty
- Error
- No matching filters
- Missing/invalid chart spec

---

## 11. Environment Variables

Create `.env.example` without real secrets.

### Pipeline / API

```dotenv
APP_ENV=development
MODEL_PATH=artifacts/model/salary_model.joblib
MODEL_METADATA_PATH=artifacts/model/model_metadata.json
LOCAL_API_BASE_URL=http://127.0.0.1:8000

OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3:8b

SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=

HTTP_TIMEOUT_SECONDS=15
LOG_LEVEL=INFO
```

### React

```dotenv
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
```

Never prefix a service-role key with `VITE_`.

---

## 12. Suggested Commands

Exact commands may change with implementation, but keep a simple developer workflow.

```bash
# Python environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# Clean data
python -m ml.src.data.clean

# Train
python -m ml.src.training.train

# Start local API
uvicorn apps.api.app.main:app --reload --port 8000

# Run pre-generation pipeline
python -m pipeline.run_pipeline

# API tests
pytest

# React app
cd apps/web
npm install
npm run dev
npm run test
npm run build
```

On Windows, use the equivalent virtual-environment activation command.

---

## 13. Git Rules

Use Git CLI only.

Recommended milestone commits:

```text
chore: initialize project structure
feat: add dataset validation and cleaning
feat: train and persist decision tree model
feat: add validated fastapi prediction service
feat: add resilient prediction batch client
feat: add ollama analysis pipeline
feat: add supabase persistence and migrations
feat: add react salary dashboard
feat: add tests and deployment configuration
docs: finalize readme and architecture
```

Do not make one enormous final commit.

---

## 14. Definition of Done

Do not call the project finished until:

- Model metrics exist.
- Prediction API is validated and tested.
- API client survives failures.
- LLM analysis is structured and validated.
- A chart renders from persisted data.
- Supabase has a published run.
- React dashboard works from a clean browser session.
- Frontend does not contain privileged keys.
- FastAPI is independently deployed.
- React is deployed.
- README contains both URLs and local setup.
- The developer can explain the code and decisions.
