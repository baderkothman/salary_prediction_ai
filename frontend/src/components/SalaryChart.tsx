import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { ChartSpec } from "../lib/schemas";
import { formatCurrency } from "../lib/format";

// Renders only the three allowlisted chart types from lib/schemas.ts's
// ChartTypeSchema. There is deliberately no dynamic component lookup keyed
// by stored data (security.md: "map chart types through an allowlist
// rather than dynamic component names from arbitrary input").
export function SalaryChart({ spec }: { spec: ChartSpec }) {
  const data = spec.x.map((label, i) => ({ label, value: spec.y[i] }));

  return (
    <figure className="salary-chart">
      <figcaption className="salary-chart__title">{spec.title}</figcaption>
      <ResponsiveContainer width="100%" height={260}>
        {spec.type === "line" ? (
          <LineChart data={data} margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
            <CartesianGrid stroke="var(--border)" vertical={false} />
            <XAxis dataKey="label" tick={{ fontSize: 12 }} stroke="var(--text-secondary)" />
            <YAxis
              tick={{ fontSize: 12 }}
              stroke="var(--text-secondary)"
              tickFormatter={(v: number) => formatCurrency(v)}
              width={80}
            />
            <Tooltip formatter={(value) => formatCurrency(Number(value))} />
            <Line type="monotone" dataKey="value" stroke="var(--primary)" strokeWidth={2} dot={{ r: 3 }} />
          </LineChart>
        ) : (
          <BarChart
            data={data}
            layout={spec.type === "horizontal_bar" ? "vertical" : "horizontal"}
            margin={{ top: 8, right: 16, left: 8, bottom: 8 }}
          >
            <CartesianGrid stroke="var(--border)" horizontal={spec.type !== "horizontal_bar"} vertical={spec.type === "horizontal_bar"} />
            {spec.type === "horizontal_bar" ? (
              <>
                <XAxis type="number" tick={{ fontSize: 12 }} stroke="var(--text-secondary)" tickFormatter={(v: number) => formatCurrency(v)} />
                <YAxis type="category" dataKey="label" tick={{ fontSize: 12 }} stroke="var(--text-secondary)" width={120} />
              </>
            ) : (
              <>
                <XAxis dataKey="label" tick={{ fontSize: 12 }} stroke="var(--text-secondary)" />
                <YAxis tick={{ fontSize: 12 }} stroke="var(--text-secondary)" tickFormatter={(v: number) => formatCurrency(v)} width={80} />
              </>
            )}
            <Tooltip formatter={(value) => formatCurrency(Number(value))} />
            <Bar dataKey="value" fill="var(--primary)" radius={4} />
          </BarChart>
        )}
      </ResponsiveContainer>
      <p className="visually-hidden">
        {spec.title}: {data.map((d) => `${d.label} ${formatCurrency(d.value)}`).join(", ")}
      </p>
    </figure>
  );
}

export function InvalidChartFallback() {
  return <p className="chart-fallback">This chart couldn't be displayed.</p>;
}
