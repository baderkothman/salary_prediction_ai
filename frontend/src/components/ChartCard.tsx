import type { ReactNode } from "react";

export function ChartCard({ children }: { children: ReactNode }) {
  return <div className="chart-card">{children}</div>;
}
