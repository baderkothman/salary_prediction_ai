export function MetricCard({
  label,
  value,
  context,
}: {
  label: string;
  value: string;
  context?: string;
}) {
  return (
    <div className="metric-card">
      <span className="metric-card__label">{label}</span>
      <span className="metric-card__value tabular-nums">{value}</span>
      {context && <span className="metric-card__context">{context}</span>}
    </div>
  );
}
