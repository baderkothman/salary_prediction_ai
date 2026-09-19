# Salary Prediction Application - Implementation Plan

## 1. Execution Rules for the Agent

Before implementation:

1. Read `prd.md`.
2. Read `architecture.md`.
3. Read `essentials.md`.
4. Read `security.md`.
5. Read `design.md`.
6. Inspect the actual dataset before hardcoding schema assumptions.
7. Create a short task checklist in the repository and update it as work proceeds.

Implementation principles:

- Work in small, testable vertical increments.
- Do not hide errors to make a step appear complete.
- Keep preprocessing in one reusable model pipeline.
- Prefer deterministic output for data preparation and sampling.
- Write tests alongside each major subsystem.
- Use Git CLI and make milestone commits.
- Do not implement features not required by the PRD until the core deliverables are complete.

---

## 2. Phase 0 - Project Bootstrap

### Tasks

- [ ] Create repository structure from `architecture.md`.
- [ ] Add Python virtual environment instructions.
- [ ] Add Python dependency files.
- [ ] Create React + Vite + TypeScript app in `apps/web`.
- [ ] Add `.gitignore`.
- [ ] Add `.env.example`.
- [ ] Create initial README skeleton.
- [ ] Add formatting/linting configuration.
- [ ] Verify Git CLI workflow.

### Exit criteria

- Python imports work.
- React dev server starts.
- No secrets are committed.
- Directory structure matches the architecture closely.

---

## 3. Phase 1 - Acquire and Inspect Dataset

### Tasks

- [ ] Download the Kaggle Data Science Job Salaries dataset or request the user to place it in `data/raw/` if credentials/manual download are required.
- [ ] Record original filename.
- [ ] Inspect columns, dtypes, row count, missing values, duplicates, unique counts, and numeric ranges.
- [ ] Confirm the prediction target.
- [ ] Identify target leakage fields.
- [ ] Identify high-cardinality features.
- [ ] Decide the final model feature set based on the real dataset.
- [ ] Generate `artifacts/reports/data_profile.json`.

### Required decision record

Document:

```text
Target:
Features included:
Features excluded:
Leakage fields:
Missing-value strategy:
Outlier policy:
High-cardinality policy:
```

### Exit criteria

No training code is written against guessed columns.

---

## 4. Phase 2 - Cleaning Pipeline

### Tasks

- [ ] Implement schema validation.
- [ ] Normalize column names only if necessary.
- [ ] Handle duplicates.
- [ ] Handle missing values.
- [ ] Validate numeric columns.
- [ ] Validate category values.
- [ ] Remove/document unusable rows.
- [ ] Write `data/processed/salaries_clean.csv`.
- [ ] Write `artifacts/reports/cleaning_report.json`.
- [ ] Add tests for deterministic cleaning and schema failure.

### Cleaning report must include

- Input row count.
- Output row count.
- Duplicate count.
- Missing-value counts before/after.
- Rows removed and reasons.
- Final feature columns.

### Exit criteria

Running the cleaning command twice on the same input produces equivalent output.

---

## 5. Phase 3 - Model Training and Evaluation

### Tasks

- [ ] Build scikit-learn preprocessing.
- [ ] Build `DecisionTreeRegressor` pipeline.
- [ ] Split train/test with fixed seed.
- [ ] Train baseline model.
- [ ] Evaluate MAE, RMSE, R².
- [ ] Inspect obvious overfitting.
- [ ] Tune a small, explainable set of tree hyperparameters if needed.
- [ ] Select final Decision Tree.
- [ ] Serialize full pipeline.
- [ ] Write model metadata JSON.
- [ ] Add load-and-predict test.

### Guardrails

- Do not use salary target leakage columns.
- Do not fit preprocessing separately on test data.
- Do not choose hyperparameters using the final test set repeatedly.
- Keep experimentation small enough to explain.

### Exit criteria

A fresh Python process can load the saved artifact and produce a finite prediction from a valid sample input.

---

## 6. Phase 4 - FastAPI Service

### Tasks

- [ ] Add configuration module.
- [ ] Load model/metadata during app startup.
- [ ] Implement `GET /health`.
- [ ] Implement `GET /api/v1/metadata`.
- [ ] Implement `GET /api/v1/predict`.
- [ ] Validate categorical values.
- [ ] Validate numeric ranges.
- [ ] Add stable error format.
- [ ] Add exception handler for unexpected errors.
- [ ] Add unit/integration tests.
- [ ] Add Dockerfile if using container deployment.

### Required tests

- [ ] Valid request.
- [ ] Missing field.
- [ ] Unsupported category.
- [ ] Invalid number.
- [ ] Model unavailable.
- [ ] Health response.

### Exit criteria

API has no unhandled error for tested invalid input categories.

---

## 7. Phase 5 - Input-Space Coverage + Python Client

### Tasks

- [ ] Generate distinct observed model-input tuples from cleaned data.
- [ ] Calculate total tuple count.
- [ ] Decide whether full observed coverage is reasonable.
- [ ] If not, implement deterministic stratified sampling.
- [ ] Write coverage report.
- [ ] Implement HTTPX client.
- [ ] Add timeout.
- [ ] Add bounded retries for transient failures.
- [ ] Capture failed inputs separately.
- [ ] Validate successful API response structure.
- [ ] Add tests using mocked HTTP responses.

### Exit criteria

The client can process a batch containing successful, invalid, and simulated failed requests without crashing the whole batch.

---

## 8. Phase 6 - Deterministic Analysis Context

### Tasks

For each prediction or useful grouping:

- [ ] Identify comparison group.
- [ ] Calculate sample size.
- [ ] Calculate mean/median.
- [ ] Calculate quartiles/percentile where meaningful.
- [ ] Build chart-ready numeric data.
- [ ] Store the context object before passing it to the LLM.

### Important

Do not ask the LLM to calculate statistics from a large raw dataset when Python can calculate them exactly.

### Exit criteria

Analysis context can be serialized to JSON and independently verified without the LLM.

---

## 9. Phase 7 - Ollama Integration

### Tasks

- [ ] Verify Ollama is installed/running or give the user the exact missing setup step.
- [ ] Make model name configurable.
- [ ] Design system + user prompt for grounded narrative.
- [ ] Require JSON output.
- [ ] Create Pydantic schema for LLM response.
- [ ] Validate headline/summary/insight lengths.
- [ ] Allow only supported chart types.
- [ ] Retry malformed output a small bounded number of times.
- [ ] Mark persistent malformed generations as failed instead of storing invalid JSON.
- [ ] Add prompt version string.

### Prompt requirements

The LLM must be told:

- Use only the supplied facts.
- Do not invent statistics.
- Do not imply causation.
- Explain the prediction relative to comparison data.
- Return only the agreed JSON schema.

### Exit criteria

A valid result produces a narrative and chart spec that pass Pydantic validation.

---

## 10. Phase 8 - Supabase Schema and Persistence

### Tasks

- [ ] Create Supabase project if not already available.
- [ ] Add migrations for `pipeline_runs` and `salary_results`.
- [ ] Add constraints and indexes.
- [ ] Enable RLS.
- [ ] Add public read-only policy for published data.
- [ ] Verify anonymous writes fail.
- [ ] Implement pipeline persistence client using service role.
- [ ] Start run with `building`.
- [ ] Upsert/insert results by feature signature.
- [ ] Store coverage/model/prompt metadata.
- [ ] Mark run `published` only after completeness checks.
- [ ] Mark unrecoverable run `failed`.

### Suggested indexes

- `salary_results(run_id)`
- `(run_id, experience_level)`
- `(run_id, employment_type)`
- `(run_id, company_size)`
- `(run_id, remote_ratio)`
- `(run_id, job_title)` if query patterns justify it

### Exit criteria

Anonymous client can read published data but cannot insert/update/delete it.

---

## 11. Phase 9 - End-to-End Local Generation

### Tasks

- [ ] Implement `pipeline/run_pipeline.py` orchestration.
- [ ] Create one run ID.
- [ ] Load cleaned data/model metadata.
- [ ] Generate input tuples.
- [ ] Call local FastAPI.
- [ ] Build deterministic context.
- [ ] Call Ollama.
- [ ] Validate analysis.
- [ ] Persist successful results.
- [ ] Persist failure counts.
- [ ] Run final completeness checks.
- [ ] Publish or fail run.

### Run summary output

At completion, print/log:

```text
run_id
model_version
attempted
prediction_success
prediction_failed
llm_success
llm_failed
persisted
status
elapsed_time
```

### Exit criteria

Supabase contains one valid `published` run with dashboard-ready records.

---

## 12. Phase 10 - React Foundation

### Tasks

- [ ] Add Supabase browser client.
- [ ] Add TanStack Query provider.
- [ ] Add React Router.
- [ ] Add design tokens/global styles.
- [ ] Create app shell/header.
- [ ] Create data schemas with Zod.
- [ ] Implement latest published run query.
- [ ] Add global loading/error/empty patterns.

### Security check

Search built frontend/environment files and confirm the Supabase service-role key is absent.

### Exit criteria

React app can display metadata for the latest published run from Supabase.

---

## 13. Phase 11 - React Overview Dashboard

### Tasks

- [ ] Page header and generation metadata.
- [ ] KPI cards.
- [ ] Primary salary chart.
- [ ] Secondary breakdown chart.
- [ ] Insight panel.
- [ ] Loading skeletons.
- [ ] No-published-run state.
- [ ] Responsive behavior.

### Exit criteria

Overview works at 360px, 768px, 1024px, and 1440px without clipping.

---

## 14. Phase 12 - Explore + Detail Experience

### Tasks

- [ ] Build filter controls from published values.
- [ ] Searchable job-title filter.
- [ ] Query/pagination strategy.
- [ ] Results table.
- [ ] Mobile results representation.
- [ ] Prediction detail route/panel.
- [ ] Narrative rendering.
- [ ] Supporting statistics.
- [ ] Recharts renderer from validated chart spec.
- [ ] Invalid-chart fallback.
- [ ] Filter empty state.

### Exit criteria

User can filter, open a result, read the prediction, inspect analysis, and view at least one chart without any call to Ollama or FastAPI from the dashboard.

---

## 15. Phase 13 - Methodology + Transparency

### Tasks

- [ ] Dataset attribution/source.
- [ ] Cleaning explanation.
- [ ] Feature list.
- [ ] Model type.
- [ ] Evaluation metrics.
- [ ] Input-space coverage approach.
- [ ] LLM grounding explanation.
- [ ] Limitations.

### Exit criteria

A reviewer can understand how the prediction reaches the dashboard without reading the source code.

---

## 16. Phase 14 - Testing and Quality Pass

### Python

- [ ] `pytest` passes.
- [ ] Clean formatting/linting.
- [ ] Model artifact load test passes.

### React

- [ ] Unit/component tests pass.
- [ ] Production build succeeds.
- [ ] No console-breaking runtime errors.
- [ ] Basic keyboard navigation checked.
- [ ] Responsive checks completed.

### Security

- [ ] RLS verified.
- [ ] Anonymous write attempt rejected.
- [ ] Secret scan/manual check.
- [ ] LLM chart schema allowlist verified.

---

## 17. Phase 15 - Deployment

### FastAPI

- [ ] Package model artifact with deployment or provide deterministic artifact retrieval during build.
- [ ] Configure environment variables.
- [ ] Deploy service.
- [ ] Verify `/health`.
- [ ] Verify valid `/api/v1/predict` request.
- [ ] Verify invalid request returns 4xx.

### React

- [ ] Configure `VITE_SUPABASE_URL`.
- [ ] Configure `VITE_SUPABASE_ANON_KEY`.
- [ ] Deploy production build.
- [ ] Verify fresh browser load.
- [ ] Verify mobile viewport.

### Exit criteria

Both deliverable URLs are reachable from outside the development machine.

---

## 18. Phase 16 - Final README and Handoff

README must include:

- Project overview.
- Architecture diagram.
- Tech stack.
- Dataset source.
- Local prerequisites.
- Dataset placement/download instructions.
- Python setup.
- Ollama setup/model configuration.
- Supabase setup/migrations.
- Training command.
- API start command.
- Generation pipeline command.
- React start/build commands.
- Test commands.
- Deployment URLs.
- Model metrics.
- Limitations.

Final verification:

- [ ] No TODO placeholder blocks remain in critical flows.
- [ ] No secrets are committed.
- [ ] Git history has meaningful commits.
- [ ] Live React URL works.
- [ ] Live FastAPI URL works.
- [ ] README is accurate against the actual repository.
- [ ] Every major architectural decision can be explained.
