import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { ChartCard } from "../components/ChartCard";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { LimitationsCallout } from "../components/LimitationsCallout";
import { LoadingSkeleton } from "../components/LoadingSkeleton";
import { NarrativeSection } from "../components/NarrativeSection";
import { PageContainer, PageHeader } from "../components/PageContainer";
import { InvalidChartFallback, SalaryChart } from "../components/SalaryChart";
import { SupportingStatistics } from "../components/SupportingStatistics";
import { ApiError, fetchModelInfo, fetchNarrative, fetchPrediction, type PredictionInputs } from "../lib/api";
import {
  COMPANY_SIZE_LABELS,
  EMPLOYMENT_TYPE_LABELS,
  EXPERIENCE_LEVEL_LABELS,
  formatCurrency,
  labelFor,
  remoteRatioLabel,
} from "../lib/format";
import { ChartSpecSchema } from "../lib/schemas";

const EMPTY_FORM: Partial<PredictionInputs> = {};

export function PredictPage() {
  const modelInfoQuery = useQuery({ queryKey: ["model-info"], queryFn: fetchModelInfo });
  const [form, setForm] = useState<Partial<PredictionInputs>>(EMPTY_FORM);
  const [submitted, setSubmitted] = useState<PredictionInputs | null>(null);

  const predictMutation = useMutation({ mutationFn: fetchPrediction });
  const narrateMutation = useMutation({ mutationFn: fetchNarrative });

  const isComplete =
    form.experience_level &&
    form.employment_type &&
    form.job_title?.trim() &&
    form.employee_residence?.trim() &&
    form.company_location?.trim() &&
    form.company_size &&
    form.work_year !== undefined &&
    form.remote_ratio !== undefined;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!isComplete) return;
    const inputs = form as PredictionInputs;
    setSubmitted(inputs);
    predictMutation.mutate(inputs);
    narrateMutation.mutate(inputs);
  }

  if (modelInfoQuery.isPending) {
    return (
      <PageContainer>
        <PageHeader title="Predict a Salary" />
        <LoadingSkeleton height={300} />
      </PageContainer>
    );
  }

  if (modelInfoQuery.isError || !modelInfoQuery.data) {
    return (
      <PageContainer>
        <PageHeader title="Predict a Salary" />
        <ErrorState message="Could not reach the prediction API. Is it running (uvicorn backend.app.main:app)?" />
      </PageContainer>
    );
  }

  const info = modelInfoQuery.data;
  const chartParsed = narrateMutation.data ? ChartSpecSchema.safeParse(narrateMutation.data.chart) : null;
  const narrativeContext = narrateMutation.data
    ? {
        comparison_group: narrateMutation.data.supporting_stats,
        percentile_rank_in_dataset: narrateMutation.data.percentile_rank_in_dataset,
      }
    : null;

  return (
    <PageContainer>
      <PageHeader
        title="Predict a Salary"
        description="Calls the live prediction API and a local Ollama model directly -- this is the one page on this dashboard that doesn't just read pre-generated data."
      />

      <form className="filter-bar" onSubmit={handleSubmit}>
        <div className="filter-bar__row">
          <label className="filter-field">
            <span className="filter-field__label">Experience</span>
            <select
              value={form.experience_level ?? ""}
              onChange={(e) => setForm({ ...form, experience_level: e.target.value || undefined })}
              required
            >
              <option value="" disabled>
                Select…
              </option>
              {info.categorical_domains.experience_level.map((v) => (
                <option key={v} value={v}>
                  {labelFor(EXPERIENCE_LEVEL_LABELS, v)} ({v})
                </option>
              ))}
            </select>
          </label>

          <label className="filter-field">
            <span className="filter-field__label">Employment</span>
            <select
              value={form.employment_type ?? ""}
              onChange={(e) => setForm({ ...form, employment_type: e.target.value || undefined })}
              required
            >
              <option value="" disabled>
                Select…
              </option>
              {info.categorical_domains.employment_type.map((v) => (
                <option key={v} value={v}>
                  {labelFor(EMPLOYMENT_TYPE_LABELS, v)} ({v})
                </option>
              ))}
            </select>
          </label>

          <label className="filter-field">
            <span className="filter-field__label">Company size</span>
            <select
              value={form.company_size ?? ""}
              onChange={(e) => setForm({ ...form, company_size: e.target.value || undefined })}
              required
            >
              <option value="" disabled>
                Select…
              </option>
              {info.categorical_domains.company_size.map((v) => (
                <option key={v} value={v}>
                  {labelFor(COMPANY_SIZE_LABELS, v)} ({v})
                </option>
              ))}
            </select>
          </label>

          <label className="filter-field">
            <span className="filter-field__label">Remote</span>
            <select
              value={form.remote_ratio ?? ""}
              onChange={(e) => setForm({ ...form, remote_ratio: e.target.value ? Number(e.target.value) : undefined })}
              required
            >
              <option value="" disabled>
                Select…
              </option>
              {info.numeric_ranges.remote_ratio.allowed_values.map((v) => (
                <option key={v} value={v}>
                  {remoteRatioLabel(v)}
                </option>
              ))}
            </select>
          </label>

          <label className="filter-field">
            <span className="filter-field__label">Work year</span>
            <input
              type="number"
              min={info.numeric_ranges.work_year.min}
              max={info.numeric_ranges.work_year.max}
              value={form.work_year ?? ""}
              onChange={(e) => setForm({ ...form, work_year: e.target.value ? Number(e.target.value) : undefined })}
              required
            />
          </label>

          <label className="filter-field filter-field--grow">
            <span className="filter-field__label">Job title</span>
            <input
              list="predict-job-titles"
              value={form.job_title ?? ""}
              onChange={(e) => setForm({ ...form, job_title: e.target.value || undefined })}
              placeholder="e.g. Data Scientist"
              required
            />
            <datalist id="predict-job-titles">
              {info.categorical_domains.job_title.map((v) => (
                <option key={v} value={v} />
              ))}
            </datalist>
          </label>

          <label className="filter-field">
            <span className="filter-field__label">Employee residence</span>
            <input
              list="predict-residences"
              value={form.employee_residence ?? ""}
              onChange={(e) => setForm({ ...form, employee_residence: e.target.value || undefined })}
              placeholder="e.g. US"
              required
            />
            <datalist id="predict-residences">
              {info.categorical_domains.employee_residence.map((v) => (
                <option key={v} value={v} />
              ))}
            </datalist>
          </label>

          <label className="filter-field">
            <span className="filter-field__label">Company location</span>
            <input
              list="predict-locations"
              value={form.company_location ?? ""}
              onChange={(e) => setForm({ ...form, company_location: e.target.value || undefined })}
              placeholder="e.g. US"
              required
            />
            <datalist id="predict-locations">
              {info.categorical_domains.company_location.map((v) => (
                <option key={v} value={v} />
              ))}
            </datalist>
          </label>

          <button type="submit" className="button" disabled={!isComplete || predictMutation.isPending}>
            {predictMutation.isPending ? "Predicting…" : "Predict"}
          </button>
        </div>
      </form>

      {submitted && (
        <div className="result-detail-grid">
          <section>
            <h2 className="section-title">Prediction</h2>
            {predictMutation.isPending && <LoadingSkeleton height={80} />}
            {predictMutation.isError && (
              <ErrorState
                message={
                  predictMutation.error instanceof ApiError
                    ? predictMutation.error.message
                    : "Could not reach the prediction API."
                }
              />
            )}
            {predictMutation.data && (
              <p className="result-detail-header__salary tabular-nums">
                {formatCurrency(predictMutation.data.prediction)} predicted salary
              </p>
            )}
          </section>

          <section>
            <h2 className="section-title">Analyst narrative (local Ollama)</h2>
            {narrateMutation.isPending && (
              <EmptyState title="Generating analysis…" description="A local model is writing this -- usually 10-25 seconds." />
            )}
            {narrateMutation.isError && (
              <ErrorState
                message={
                  narrateMutation.error instanceof ApiError
                    ? narrateMutation.error.message
                    : "Could not generate a narrative."
                }
              />
            )}
            {narrateMutation.data && (
              <NarrativeSection
                headline={narrateMutation.data.headline}
                summary={narrateMutation.data.summary}
                insights={narrateMutation.data.insights}
                comparison={narrateMutation.data.comparison}
              />
            )}
          </section>
        </div>
      )}

      {chartParsed?.success && (
        <ChartCard>
          <SalaryChart spec={chartParsed.data} />
        </ChartCard>
      )}
      {narrateMutation.data && chartParsed && !chartParsed.success && <InvalidChartFallback />}

      {narrativeContext && <SupportingStatistics context={narrativeContext} />}

      {narrateMutation.data?.limitations && <LimitationsCallout limitations={narrateMutation.data.limitations} />}
    </PageContainer>
  );
}
