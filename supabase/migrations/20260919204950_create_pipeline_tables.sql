-- Pipeline runs: one row per generation-pipeline execution. A run starts as
-- 'building' and only becomes 'published' after completeness checks pass in
-- scripts/persist.py -- the React dashboard must only ever read published
-- runs (architecture.md invariant #9: partial pipeline runs are not published).
create table if not exists public.pipeline_runs (
    id uuid primary key default gen_random_uuid(),
    status text not null default 'building' check (status in ('building', 'published', 'failed')),
    model_version text not null,
    dataset_hash text not null,
    llm_model text not null,
    prompt_version text not null,
    model_metrics jsonb not null,
    coverage_summary jsonb,
    created_at timestamptz not null default now(),
    published_at timestamptz
);

comment on table public.pipeline_runs is
    'One row per local generation-pipeline execution. Dashboard-facing queries must filter to status = ''published''.';

-- Dashboard-ready results: one row per distinct observed feature tuple for a
-- given run, including the prediction and its validated LLM narrative/chart.
create table if not exists public.salary_results (
    id uuid primary key default gen_random_uuid(),
    run_id uuid not null references public.pipeline_runs(id) on delete cascade,
    feature_signature text not null,

    work_year integer,
    experience_level text not null,
    employment_type text not null,
    job_title text not null,
    employee_residence text,
    remote_ratio integer,
    company_location text,
    company_size text not null,

    features jsonb not null,
    predicted_salary_usd numeric not null check (predicted_salary_usd >= 0),

    analysis_headline text,
    analysis_summary text,
    key_insights jsonb,
    chart_spec jsonb,
    analysis_context jsonb,
    limitations jsonb,

    created_at timestamptz not null default now(),

    constraint salary_results_run_feature_unique unique (run_id, feature_signature),
    constraint salary_results_remote_ratio_valid check (remote_ratio is null or remote_ratio in (0, 50, 100))
);

comment on table public.salary_results is
    'Dashboard-ready predictions + validated LLM analysis for one pipeline run. Never insert here for a run that is not still building.';

create index if not exists idx_salary_results_run_id on public.salary_results (run_id);
create index if not exists idx_salary_results_run_experience on public.salary_results (run_id, experience_level);
create index if not exists idx_salary_results_run_employment on public.salary_results (run_id, employment_type);
create index if not exists idx_salary_results_run_company_size on public.salary_results (run_id, company_size);
create index if not exists idx_salary_results_run_remote_ratio on public.salary_results (run_id, remote_ratio);
create index if not exists idx_salary_results_run_job_title on public.salary_results (run_id, job_title);

-- Row Level Security: the browser (anon key) may only ever read published
-- data, and can never write. The pipeline writes with the service_role key,
-- which bypasses RLS entirely by Supabase's design -- no write policy is
-- needed or added for anon/authenticated.
alter table public.pipeline_runs enable row level security;
alter table public.salary_results enable row level security;

create policy "public can read published runs"
    on public.pipeline_runs
    for select
    to anon, authenticated
    using (status = 'published');

create policy "public can read results of published runs"
    on public.salary_results
    for select
    to anon, authenticated
    using (
        exists (
            select 1 from public.pipeline_runs pr
            where pr.id = salary_results.run_id
              and pr.status = 'published'
        )
    );
