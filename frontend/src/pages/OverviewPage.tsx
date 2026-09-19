import { ChartCard } from "../components/ChartCard";
import { CardSkeleton, LoadingSkeleton } from "../components/LoadingSkeleton";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { MetricCard } from "../components/MetricCard";
import { PageContainer, PageHeader } from "../components/PageContainer";
import { SalaryChart } from "../components/SalaryChart";
import { formatCurrency, formatDateTime, labelFor, EXPERIENCE_LEVEL_LABELS, COMPANY_SIZE_LABELS } from "../lib/format";
import { useLatestPublishedRun, useOverviewStats } from "../lib/queries";
import type { ChartSpec } from "../lib/schemas";

export function OverviewPage() {
  const runQuery = useLatestPublishedRun();
  const statsQuery = useOverviewStats(runQuery.data?.id);

  if (runQuery.isPending) {
    return (
      <PageContainer>
        <PageHeader title="Salary Prediction Landscape" />
        <div className="kpi-grid">
          {Array.from({ length: 4 }).map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      </PageContainer>
    );
  }

  if (runQuery.isError) {
    return (
      <PageContainer>
        <ErrorState message={runQuery.error instanceof Error ? runQuery.error.message : undefined} />
      </PageContainer>
    );
  }

  if (!runQuery.data) {
    return (
      <PageContainer>
        <PageHeader title="Salary Prediction Landscape" />
        <EmptyState
          title="No published salary dataset is available yet"
          description="Run the generation pipeline and publish a completed run to see predictions here."
        />
      </PageContainer>
    );
  }

  const run = runQuery.data;

  const experienceChart: ChartSpec | null = statsQuery.data
    ? {
        type: "bar",
        title: "Median predicted salary by experience level",
        x: statsQuery.data.byExperienceLevel.map((d) => labelFor(EXPERIENCE_LEVEL_LABELS, d.label)),
        y: statsQuery.data.byExperienceLevel.map((d) => d.value),
      }
    : null;

  const companySizeChart: ChartSpec | null = statsQuery.data
    ? {
        type: "horizontal_bar",
        title: "Median predicted salary by company size",
        x: statsQuery.data.byCompanySize.map((d) => labelFor(COMPANY_SIZE_LABELS, d.label)),
        y: statsQuery.data.byCompanySize.map((d) => d.value),
      }
    : null;

  return (
    <PageContainer>
      <PageHeader
        title="Salary Prediction Landscape"
        description={`Last generated ${formatDateTime(run.published_at ?? run.created_at)} · Model ${run.model_version}`}
      />

      <div className="kpi-grid">
        {statsQuery.data ? (
          <>
            <MetricCard label="Generated predictions" value={String(statsQuery.data.count)} />
            <MetricCard label="Median predicted salary" value={formatCurrency(statsQuery.data.medianSalary)} />
            <MetricCard
              label="Salary range"
              value={`${formatCurrency(statsQuery.data.minSalary)} – ${formatCurrency(statsQuery.data.maxSalary)}`}
            />
            <MetricCard label="Job titles represented" value={String(statsQuery.data.distinctJobTitles)} />
          </>
        ) : (
          Array.from({ length: 4 }).map((_, i) => <CardSkeleton key={i} />)
        )}
      </div>

      <div className="overview-charts">
        <ChartCard>
          {experienceChart ? <SalaryChart spec={experienceChart} /> : <LoadingSkeleton height={260} />}
        </ChartCard>
        <ChartCard>
          {companySizeChart ? <SalaryChart spec={companySizeChart} /> : <LoadingSkeleton height={260} />}
        </ChartCard>
      </div>

      <div className="model-metrics-note">
        <span>Model evaluation (held-out test set): </span>
        MAE {formatCurrency(run.model_metrics.mae)} · RMSE {formatCurrency(run.model_metrics.rmse)} · R²{" "}
        {run.model_metrics.r2.toFixed(2)}
      </div>
    </PageContainer>
  );
}
