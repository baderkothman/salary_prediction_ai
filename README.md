# Salary Prediction Application

End-to-end ML salary prediction system for data-science jobs: a scikit-learn Decision Tree model served over FastAPI, a local-Ollama analysis pipeline, Supabase persistence, and a React + Vite + TypeScript dashboard.

> Status: under active implementation, phase by phase. This README is updated as each phase lands; see `plan.md` for the full phase list and `essentials.md` for the fast-start contract.

## Documentation

Read in this order before changing anything:

1. [`prd.md`](prd.md) — product requirements
2. [`architecture.md`](architecture.md) — system design and invariants
3. [`essentials.md`](essentials.md) — condensed fast-start contract
4. [`security.md`](security.md) — trust boundaries and secret handling
5. [`design.md`](design.md) — UI direction
6. [`plan.md`](plan.md) — phased execution plan
7. [`CLAUDE.md`](CLAUDE.md) — guidance for AI coding agents working in this repo

## Repository structure

```text
frontend/   React + Vite + TypeScript dashboard
backend/    FastAPI prediction service (independently deployable)
ml/         Data cleaning, feature engineering, Decision Tree training, evaluation
scripts/    Local generation pipeline: input-space coverage, API client, Ollama analysis, Supabase persistence
docs/       Generated reports (dataset inspection, cleaning, evaluation)
```

## Local setup

### Prerequisites

- Python 3.11+ (developed against 3.14)
- Node.js 20+
- [Ollama](https://ollama.com) running locally with a pulled model
- A Supabase project (for persistence, from Phase 9 onward)

### Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Environment variables

```bash
cp .env.example .env
# fill in SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY
```

Commands for training, running the API, and running the generation pipeline will be documented here as each phase is implemented.

## Deployment

The FastAPI service and the React dashboard are deployed independently; the dashboard reads only from Supabase at runtime and does not depend on Ollama, the local pipeline, or the FastAPI service. Deployment URLs will be added here once available.
