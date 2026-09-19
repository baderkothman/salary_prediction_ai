import { useState } from "react";

import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { FilterBar } from "../components/FilterBar";
import { TableSkeletonRows } from "../components/LoadingSkeleton";
import { PageContainer, PageHeader } from "../components/PageContainer";
import { ResultsTable } from "../components/ResultsTable";
import { formatCurrency } from "../lib/format";
import { PAGE_SIZE, useFilterOptions, useLatestPublishedRun, useSalaryResults, type ResultFilters } from "../lib/queries";
import { median } from "../lib/stats";

export function ExplorePage() {
  const runQuery = useLatestPublishedRun();
  const runId = runQuery.data?.id;
  const optionsQuery = useFilterOptions(runId);

  const [filters, setFilters] = useState<ResultFilters>({});
  const [page, setPage] = useState(0);

  const resultsQuery = useSalaryResults(runId, filters, page);

  const handleFilterChange = (next: ResultFilters) => {
    setFilters(next);
    setPage(0);
  };

  if (runQuery.isPending) {
    return (
      <PageContainer>
        <PageHeader title="Explore Predictions" />
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

  if (!runId) {
    return (
      <PageContainer>
        <PageHeader title="Explore Predictions" />
        <EmptyState
          title="No published salary dataset is available yet"
          description="Run the generation pipeline and publish a completed run to explore predictions here."
        />
      </PageContainer>
    );
  }

  const totalPages = resultsQuery.data ? Math.ceil(resultsQuery.data.total / PAGE_SIZE) : 0;
  const medianOfPage = resultsQuery.data ? median(resultsQuery.data.rows.map((r) => r.predicted_salary_usd)) : 0;

  return (
    <PageContainer>
      <PageHeader title="Explore Predictions" description="Filter by role, seniority, company size, and remote arrangement." />

      {optionsQuery.data && <FilterBar options={optionsQuery.data} filters={filters} onChange={handleFilterChange} />}

      {resultsQuery.isError && <ErrorState message={resultsQuery.error instanceof Error ? resultsQuery.error.message : undefined} />}

      {resultsQuery.data && (
        <p className="results-summary">
          {resultsQuery.data.total} matching predictions
          {resultsQuery.data.rows.length > 0 && <> · Median {formatCurrency(medianOfPage)} on this page</>}
        </p>
      )}

      {resultsQuery.data && resultsQuery.data.total === 0 ? (
        <EmptyState title="No predictions match these filters" description="Try removing one or more filters." />
      ) : (
        <>
          <ResultsTable results={resultsQuery.data?.rows ?? []} />
          {resultsQuery.isLoading && (
            <table className="results-table results-table--desktop">
              <tbody>
                <TableSkeletonRows />
              </tbody>
            </table>
          )}

          {totalPages > 1 && (
            <div className="pagination">
              <button className="button button--ghost" disabled={page === 0} onClick={() => setPage((p) => p - 1)}>
                Previous
              </button>
              <span>
                Page {page + 1} of {totalPages}
              </span>
              <button
                className="button button--ghost"
                disabled={page + 1 >= totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </PageContainer>
  );
}
