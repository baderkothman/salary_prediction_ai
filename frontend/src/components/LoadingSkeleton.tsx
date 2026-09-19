export function LoadingSkeleton({ height = 16, width = "100%" }: { height?: number; width?: string | number }) {
  return <div className="skeleton" style={{ height, width }} aria-hidden="true" />;
}

export function CardSkeleton() {
  return (
    <div className="metric-card">
      <LoadingSkeleton height={12} width="60%" />
      <div style={{ height: 8 }} />
      <LoadingSkeleton height={28} width="80%" />
    </div>
  );
}

export function TableSkeletonRows({ rows = 5 }: { rows?: number }) {
  return (
    <>
      {Array.from({ length: rows }).map((_, i) => (
        <tr key={i}>
          <td colSpan={6}>
            <LoadingSkeleton height={20} />
          </td>
        </tr>
      ))}
    </>
  );
}
