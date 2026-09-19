import { formatCurrency } from "../lib/format";

interface ComparisonGroup {
  description?: string;
  sample_size?: number;
  mean_salary_usd?: number;
  median_salary_usd?: number;
  p25_salary_usd?: number;
  p75_salary_usd?: number;
}

// analysis_context is stored as an untyped JSONB blob (it's an internal
// computation record, not user-facing API surface), so this reads it
// defensively rather than asserting a strict schema -- a missing/renamed
// field just means that stat isn't shown, not a crash.
export function SupportingStatistics({ context }: { context: Record<string, unknown> | null }) {
  if (!context) return null;

  const group = context.comparison_group as ComparisonGroup | undefined;
  const percentile = context.percentile_rank_in_dataset as number | undefined;

  if (!group) return null;

  const stats: [string, string][] = [];
  if (group.description) stats.push(["Peer group", group.description]);
  if (group.sample_size !== undefined) stats.push(["Sample size", String(group.sample_size)]);
  if (group.median_salary_usd !== undefined) stats.push(["Peer median", formatCurrency(group.median_salary_usd)]);
  if (group.mean_salary_usd !== undefined) stats.push(["Peer mean", formatCurrency(group.mean_salary_usd)]);
  if (group.p25_salary_usd !== undefined && group.p75_salary_usd !== undefined) {
    stats.push(["Peer 25th–75th percentile", `${formatCurrency(group.p25_salary_usd)} – ${formatCurrency(group.p75_salary_usd)}`]);
  }
  if (percentile !== undefined) stats.push(["Percentile in full dataset", `${percentile}th`]);

  if (stats.length === 0) return null;

  return (
    <div className="supporting-stats">
      <span className="supporting-stats__title">Supporting statistics</span>
      <dl className="context-grid">
        {stats.map(([term, value]) => (
          <div className="context-grid__item" key={term}>
            <dt>{term}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
