# Salary Prediction Application - Product Requirements Document

## 1. Product Summary

Build and deploy an end-to-end machine-learning salary prediction application for data-science jobs.

The system must:

1. Clean and prepare the Kaggle **Data Science Job Salaries** dataset.
2. Train a **Decision Tree regression model** to predict salary in USD.
3. Expose the trained model through a validated **FastAPI GET prediction endpoint**.
4. Provide a Python client that calls the prediction API without unhandled failures.
5. Use a **local LLM through Ollama** to generate useful, data-grounded salary analysis and a visualization specification.
6. Persist pre-generated prediction results and analyses to **Supabase**.
7. Present those persisted results in a deployed **React website** instead of Streamlit.
8. Deploy the FastAPI prediction service independently as a separate deliverable using the same trained model artifact.

The React application is a **consumption layer**. It reads persisted results from Supabase and does not need the FastAPI service or Ollama to render the dashboard.

---

## 2. Source Dataset

Primary dataset:

- Kaggle: `ruchi798/data-science-job-salaries`
- Expected source URL: `https://www.kaggle.com/datasets/ruchi798/data-science-job-salaries`

The implementation must inspect the downloaded dataset before assuming its exact columns or category values.

Likely columns include:

- `work_year`
- `experience_level`
- `employment_type`
- `job_title`
- `salary`
- `salary_currency`
- `salary_in_usd`
- `employee_residence`
- `remote_ratio`
- `company_location`
- `company_size`

### Prediction target

Default target: `salary_in_usd`.

Salary-related leakage columns such as raw salary and salary currency must not be used as predictors for `salary_in_usd` unless a documented reason proves they do not leak the target.

---

## 3. Product Goals

### Primary goals

- Demonstrate a complete ML pipeline from raw data to deployed application.
- Produce reproducible and explainable salary predictions.
- Demonstrate correct API design and validation.
- Demonstrate local LLM integration without sending salary data to an external LLM provider.
- Produce useful narrative analysis rather than generic prose.
- Produce at least one visualization for salary analysis.
- Persist results in a schema designed for dashboard consumption.
- Provide a polished React dashboard that works on desktop, tablet, and mobile.
- Keep the independently deployed FastAPI service functional even when the React dashboard is unavailable.

### Secondary goals

- Version the model and pipeline output.
- Make failed pipeline steps recoverable.
- Make the codebase understandable enough that every important line and architectural decision can be explained.

---

## 4. Non-Goals

The first release does **not** require:

- User authentication.
- User accounts or saved personal profiles.
- Real-time LLM generation from the React website.
- React-to-FastAPI prediction requests as part of the dashboard flow.
- Deep learning models.
- Multiple ML algorithms in production.
- Training the LLM.
- A full MLOps platform.
- Payment or subscription features.

Optional model comparisons may be used during experimentation, but the required production model is the Decision Tree model.

---

## 5. Primary Users

### Dashboard visitor

Wants to explore salary predictions and understand how salary varies across role, seniority, company size, geography, employment type, and remote-work level.

### Reviewer / instructor

Wants to verify that the project includes dataset preparation, model training, API validation, robust API consumption, local LLM analysis, persistence, deployment, and a usable dashboard.

### Developer

Needs a project structure that can be run locally, tested, understood, and deployed without hidden manual steps.

---

## 6. Core User Experience

### Flow A - Explore salary landscape

1. User opens the React dashboard.
2. Dashboard loads the latest published pipeline run from Supabase.
3. User sees high-level statistics such as prediction count, median predicted salary, salary range, and model version.
4. User filters results by available dimensions.
5. Charts and the results table update.
6. User selects a prediction/result.
7. User sees the predicted salary, input attributes, LLM-generated narrative, supporting metrics, and the generated chart.

### Flow B - Review methodology

1. User opens the Methodology/About section.
2. User can see the dataset source, model type, model evaluation metrics, model version, LLM model name, and data-generation timestamp.
3. User is informed that predictions are estimates, not compensation guarantees.

### Flow C - Test deployed API

1. Reviewer calls the deployed FastAPI GET endpoint with valid query parameters.
2. API validates inputs.
3. API returns a salary prediction plus model metadata.
4. Invalid or unsupported values return a structured 4xx response rather than an unhandled server error.

---

## 7. Functional Requirements

### FR-01 - Dataset ingestion

- Download or manually place the Kaggle dataset in `data/raw/`.
- Never modify the raw source file in place.
- Record dataset filename, row count, column list, and a content hash.

### FR-02 - Data cleaning

The cleaning stage must:

- Detect duplicate rows.
- Report missing values.
- Normalize column names if needed.
- Coerce numeric columns safely.
- Validate categorical values.
- Remove or document impossible values.
- Remove target leakage features.
- Produce a deterministic cleaned dataset in `data/processed/`.
- Write a machine-readable cleaning report.

Missing values must be handled by an explicit strategy. Rows must not be silently dropped without logging counts and reasons.

### FR-03 - Feature engineering and preprocessing

- Separate categorical and numeric features.
- Use a scikit-learn `Pipeline` and `ColumnTransformer` so preprocessing and the model are serialized together.
- Encode categorical variables consistently.
- Preserve feature metadata needed by API validation and the generation pipeline.

### FR-04 - Decision Tree model training

- Train a `DecisionTreeRegressor`.
- Use a train/test split with a fixed random seed.
- Report at minimum:
  - MAE
  - RMSE
  - R²
- Prevent training/test leakage.
- Save the fitted pipeline with `joblib`.
- Save model metadata separately as JSON.
- Version the artifact.

Hyperparameters should be intentional. At minimum consider `max_depth`, `min_samples_split`, `min_samples_leaf`, and `random_state`.

### FR-05 - Prediction API

Create a FastAPI service with a GET prediction endpoint.

Recommended endpoint:

`GET /api/v1/predict`

Requirements:

- Validate all query parameters using Pydantic/FastAPI types.
- Validate categorical values against model metadata or explicitly supported values.
- Return HTTP 422 for validation errors.
- Return a stable JSON response contract.
- Include model version in successful responses.
- Add `GET /health`.
- Add `GET /api/v1/metadata` for allowed input values and model metadata.
- No raw Python stack trace may be returned to callers.

Example response shape:

```json
{
  "prediction": {
    "salary_usd": 128500.0,
    "currency": "USD"
  },
  "model": {
    "name": "decision_tree_salary_regressor",
    "version": "2026-09-19.1"
  },
  "input": {
    "experience_level": "SE",
    "employment_type": "FT",
    "job_title": "Data Scientist",
    "remote_ratio": 100,
    "company_size": "M"
  }
}
```

### FR-06 - Python API client

Provide a Python script that calls the API.

It must:

- Use timeouts.
- Retry only appropriate transient failures.
- Handle connection failures.
- Handle 4xx and 5xx responses.
- Validate returned JSON.
- Never terminate the entire batch because one request failed.
- Log failed inputs for review/retry.

### FR-07 - Input-space coverage

Do not create a naive Cartesian product of every categorical feature if it produces unrealistic or extremely large combinations.

Default strategy:

1. Build the set of **distinct valid feature tuples observed in the cleaned dataset**.
2. Deduplicate those tuples.
3. Call the prediction API once per unique tuple.
4. Track success/failure for every tuple.

This covers the observed data space without fabricating invalid combinations. If the total is still too large, create a documented deterministic sampling strategy that preserves coverage across each categorical dimension.

### FR-08 - Local LLM analysis

Use Ollama locally. The model name must be configurable through an environment variable.

For each prediction or analysis group, provide the LLM with computed facts such as:

- Predicted salary.
- Median and mean for comparable records.
- Relevant percentile or rank.
- Sample size.
- Salary distribution by one meaningful category.

The LLM must return structured JSON containing:

- `headline`
- `summary`
- `key_insights[]`
- `chart`
- `limitations[]`

The LLM must be instructed not to invent statistics that are not present in its input context.

### FR-09 - Visualization generation

At least one visualization must accompany the narrative.

Preferred approach:

- LLM chooses a chart type and narrative focus from approved options.
- Application supplies/validates the numeric data.
- LLM returns a constrained chart specification.
- React renders the chart using Recharts.

Allowed initial chart types:

- Bar chart
- Horizontal bar chart
- Line chart when the x-axis is ordered/time-based
- Distribution/histogram-like bar chart

Do not execute arbitrary code generated by the LLM.

### FR-10 - Supabase persistence

Persist pipeline outputs to Supabase.

The persisted records must support:

- Identifying a pipeline/model run.
- Filtering by major job attributes.
- Retrieving the prediction.
- Retrieving LLM narrative.
- Retrieving chart specification/data.
- Recording model and prompt versions.
- Recording timestamps.
- Distinguishing incomplete runs from published runs.

### FR-11 - React dashboard

Replace Streamlit with a **React + Vite + TypeScript** website.

The dashboard must consume **Supabase only** for application data.

Required views/features:

- Overview dashboard.
- Filter controls.
- Salary visualization section.
- Prediction/results table.
- Prediction detail panel/page.
- LLM narrative section.
- LLM-generated chart rendering.
- Empty state.
- Loading state.
- Error state.
- Methodology/model information.
- Responsive layout.

### FR-12 - Independent FastAPI deployment

Deploy the FastAPI prediction service independently.

- It uses the same versioned trained model artifact.
- It is not required by the React dashboard runtime.
- It must expose a publicly reachable URL for evaluation.

---

## 8. Data Quality Requirements

- The pipeline must fail fast if the target column is missing.
- Missing feature columns must produce a clear error.
- Numeric ranges must be validated.
- Category domains used by the API must come from model/dataset metadata, not duplicated manually across files.
- Every data-cleaning transformation must be reproducible.
- The raw dataset must remain immutable.

---

## 9. LLM Quality Requirements

The narrative is considered useful only if it:

- Refers to concrete provided values.
- Explains relative position, not only the absolute prediction.
- Connects at least two meaningful job attributes to the result when data supports it.
- Mentions sample-size or uncertainty limitations where relevant.
- Avoids causal claims such as "X causes higher salary" when the dataset only shows association.
- Avoids generic filler.

---

## 10. UX Requirements

- First meaningful dashboard content should be visible without unnecessary scrolling on desktop.
- Filters must have human-readable labels rather than raw codes only.
- Raw category codes may be shown secondarily for transparency.
- Monetary values use USD formatting.
- Tables support pagination or virtualized display if the dataset is large.
- Charts include title, axis labels, tooltip, and accessible textual context.
- The interface must work at common desktop widths and down to mobile widths.

---

## 11. Performance Requirements

- Dashboard initial data loading should avoid downloading the entire table if not required.
- Supabase queries should use pagination and indexed filter columns.
- React should cache/reuse queries where practical.
- FastAPI should load the model once on startup, not once per request.
- Ollama generation occurs in the pre-generation pipeline, never during normal dashboard page rendering.

---

## 12. Reliability Requirements

- A single bad API input may not stop the generation batch.
- A single malformed LLM response should be retried or marked failed without corrupting the run.
- Partial pipeline runs may not be exposed as the latest published dashboard dataset.
- Pipeline status must be persisted.
- Logs must identify stage, run ID, and error context without exposing secrets.

---

## 13. Acceptance Criteria

The project is complete when all of the following are true:

- [ ] Dataset cleaning script produces a reproducible processed dataset.
- [ ] Decision Tree model trains successfully.
- [ ] Evaluation metrics are stored and documented.
- [ ] Serialized model pipeline can be loaded in a fresh process.
- [ ] FastAPI GET prediction endpoint validates all inputs.
- [ ] Invalid inputs return controlled errors.
- [ ] Python API client handles network and API failures without unhandled exceptions.
- [ ] Observed input space is covered or a documented deterministic sampling policy is used.
- [ ] Ollama produces structured, data-grounded narrative output.
- [ ] At least one valid chart specification is generated and displayed.
- [ ] Results are persisted in Supabase.
- [ ] Incomplete runs are not treated as published data.
- [ ] React dashboard reads persisted data from Supabase only.
- [ ] React dashboard has loading, empty, and error states.
- [ ] React dashboard is responsive.
- [ ] Independent FastAPI service is deployed and reachable.
- [ ] React site is deployed and reachable.
- [ ] README includes setup, architecture, commands, environment variables, and deployment URLs.
- [ ] Git is used through the CLI rather than GitHub Desktop.
- [ ] The developer can explain the implementation and architectural choices.

---

## 14. Final Deliverables

1. Live URL for the React salary dashboard.
2. Live URL for the independently deployed FastAPI prediction endpoint.
3. Well-presented `README.md`.
4. Source code and Git history.
5. Versioned model artifact and metadata, or a documented reproducible method to build them if binary artifacts are excluded from Git.
6. Supabase schema/migrations.
7. These project specification documents.
