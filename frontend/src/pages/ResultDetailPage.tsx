import { useParams } from "react-router-dom";

import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { ChartCard } from "../components/ChartCard";
import { InvalidChartFallback, SalaryChart } from "../components/SalaryChart";
import { LimitationsCallout } from "../components/LimitationsCallout";
import { LoadingSkeleton } from "../components/LoadingSkeleton";
import { NarrativeSection } from "../components/NarrativeSection";
import { PageContainer } from "../components/PageContainer";
import { PredictionContextGrid } from "../components/PredictionContextGrid";
import { SupportingStatistics } from "../components/SupportingStatistics";
import { EMPLOYMENT_TYPE_LABELS, COMPANY_SIZE_LABELS, EXPERIENCE_LEVEL_LABELS, formatCurrency, labelFor, remoteRatioLabel } from "../lib/format";
import { useSalaryResult } from "../lib/queries";
import { ChartSpecSchema } from "../lib/schemas";

export function ResultDetailPage() {
  const { id } = useParams<{ id: string }>();
  const query = useSalaryResult(id);

  if (query.isPending) {
    return (
      <PageContainer>
        <LoadingSkeleton height={40} width="60%" />
        <div style={{ height: 16 }} />
        <LoadingSkeleton height={200} />
      </PageContainer>
    );
  }

  if (query.isError) {
    return (
      <PageContainer>
        <ErrorState message={query.error instanceof Error ? query.error.message : undefined} />
      </PageContainer>
    );
  }

  const result = query.data;
  if (!result) {
    return (
      <PageContainer>
        <EmptyState title="Prediction not found" description="This result may belong to a run that is no longer published." />
      </PageContainer>
    );
  }

  const hasNarrative = Boolean(result.analysis_headline && result.analysis_summary);
  const chartParsed = result.chart_spec ? ChartSpecSchema.safeParse(result.chart_spec) : null;

  return (
    <PageContainer>
      <div className="result-detail-header">
        <h1>{result.job_title}</h1>
        <p className="result-detail-header__subtitle">
          {labelFor(EXPERIENCE_LEVEL_LABELS, result.experience_level)} · {labelFor(EMPLOYMENT_TYPE_LABELS, result.employment_type)} ·{" "}
          {labelFor(COMPANY_SIZE_LABELS, result.company_size)} company
          {result.remote_ratio !== null && <> · {remoteRatioLabel(result.remote_ratio)}</>}
        </p>
        <p className="result-detail-header__salary tabular-nums">{formatCurrency(result.predicted_salary_usd)} predicted salary</p>
      </div>

      <div className="result-detail-grid">
        <section>
          <h2 className="section-title">Prediction inputs</h2>
          <PredictionContextGrid result={result} />
        </section>

        <section>
          <h2 className="section-title">Analyst narrative</h2>
          {hasNarrative ? (
            <NarrativeSection
              headline={result.analysis_headline as string}
              summary={result.analysis_summary as string}
              insights={result.key_insights ?? []}
              comparison={(result.analysis_context as Record<string, unknown> | null)?.comparison as string | undefined}
            />
          ) : (
            <EmptyState
              title="No narrative generated for this prediction"
              description="This run samples a subset of predictions for full LLM analysis; this one only has a direct model prediction."
            />
          )}
        </section>
      </div>

      {chartParsed?.success && (
        <ChartCard>
          <SalaryChart spec={chartParsed.data} />
        </ChartCard>
      )}
      {result.chart_spec && chartParsed && !chartParsed.success && <InvalidChartFallback />}

      <SupportingStatistics context={result.analysis_context} />

      {result.limitations && <LimitationsCallout limitations={result.limitations} />}
    </PageContainer>
  );
}
